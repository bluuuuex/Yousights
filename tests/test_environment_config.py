"""Offline startup and provider-secret regressions; no external services."""
import importlib.util
import os
from pathlib import Path
import runpy
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

from flask import Flask

ROOT = Path(__file__).parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EnvironmentConfigurationTests(unittest.TestCase):
    def test_provider_secrets_work_without_private_files(self):
        with patch.dict(os.environ, {
            "YOUSIGHTS_EVENTBRITE_API_KEY": "synthetic-event-key",
            "YOUSIGHTS_MEETUP_CLIENT_ID": "synthetic-id",
            "YOUSIGHTS_MEETUP_CLIENT_SECRET": "synthetic-secret",
            "YOUSIGHTS_MEETUP_REFRESH_TOKEN": "synthetic-token",
        }, clear=True), patch("builtins.open", side_effect=AssertionError("Private file must not be read")):
            eventbrite = load_module("eventbrite_env_test", "eventsAPI/eventbrite.py")
            meetup = load_module("meetup_env_test", "eventsAPI/meetup.py")
            self.assertEqual(eventbrite.get_api_key(), "synthetic-event-key")
            self.assertEqual(meetup.get_api_credentials(), {
                "client_id": "synthetic-id", "client_secret": "synthetic-secret", "refresh_token": "synthetic-token"})

    def test_missing_or_partial_provider_configuration_fails_closed(self):
        eventbrite = load_module("eventbrite_missing_test", "eventsAPI/eventbrite.py")
        meetup = load_module("meetup_missing_test", "eventsAPI/meetup.py")
        with patch.dict(os.environ, {}, clear=True), patch("os.path.isfile", return_value=False):
            with self.assertRaises(RuntimeError):
                eventbrite.get_api_key()
            with self.assertRaises(RuntimeError):
                meetup.get_api_credentials()
        with patch.dict(os.environ, {"YOUSIGHTS_MEETUP_CLIENT_ID": "synthetic-partial"}, clear=True), patch("builtins.open", side_effect=AssertionError("Must not fall back")):
            with self.assertRaises(RuntimeError):
                meetup.get_api_credentials()

    def test_youtube_keys_support_environment_and_reject_missing_secrets(self):
        shim = {"__init__": types.SimpleNamespace(credentials={"credentials": {}}),
                "sources": types.SimpleNamespace(dict_tools=types.SimpleNamespace())}
        with patch.dict(sys.modules, shim):
            youtube = load_module("youtube_env_test", "youtubeData/sources/youtube_basic.py")
        with patch.dict(os.environ, {"YOUSIGHTS_YOUTUBE_API_KEYS": "synthetic-one, synthetic-two"}, clear=True):
            self.assertEqual(youtube.get_youtube_api_keys(), ["synthetic-one", "synthetic-two"])
        with patch.dict(os.environ, {}, clear=True), patch.object(youtube.requests, "get") as request:
            with self.assertRaises(youtube.YouTubeBasicOperationException):
                youtube.youtube_video_basic_search("synthetic query")
            request.assert_not_called()

    def test_youtube_init_does_not_require_ignored_credentials_file(self):
        real_isfile = os.path.isfile
        private_file = ROOT / "youtubeData/config/credentials.json"
        with patch.dict(os.environ, {"YOUSIGHTS_MONGODB_URI": "mongodb://127.0.0.1/synthetic"}, clear=True), patch("pymongo.MongoClient", return_value=MagicMock()), patch("logging.config.dictConfig"), patch("os.path.isfile", side_effect=lambda path: False if Path(path) == private_file else real_isfile(path)):
            module = load_module("youtube_init_env_test", "youtubeData/__init__.py")
        self.assertEqual(module.credentials, {"credentials": {}})

    def test_frontend_binds_locally_and_on_explicit_platform_port(self):
        for environment, expected in [({}, "127.0.0.1"), ({"PORT": "8080"}, "0.0.0.0"), ({"PORT": "8080", "YOUSIGHTS_HOST": "127.0.0.1"}, "127.0.0.1")]:
            with patch.dict(os.environ, environment, clear=True), patch.dict(sys.modules, {"version": types.SimpleNamespace(__version__="synthetic")}), patch.object(Flask, "run") as run:
                runpy.run_path(str(ROOT / "yousights-fe/server.py"), run_name="__main__")
                self.assertEqual(run.call_args.kwargs["host"], expected)
                self.assertFalse(run.call_args.kwargs["debug"])

    def test_cloud_deployment_is_disabled_without_explicit_manual_gate(self):
        deploy = load_module("deploy_env_test", "deploy_apps.py")
        with patch.dict(os.environ, {"MERGE_PULL_REQUEST": "true"}, clear=True), patch.object(deploy.subprocess, "run") as command:
            with self.assertRaisesRegex(RuntimeError, "Cloud deployment disabled"):
                deploy.main()
            command.assert_not_called()
