import ast
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch
from flask import Flask
from flask_restx import Api
ROOT=Path(__file__).parents[1]

def load_function(path,name,namespace):
    tree=ast.parse((ROOT/path).read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),path,"exec"),namespace)
    return namespace[name]

class SecurityTests(unittest.TestCase):
    def test_database_secret_required_and_timeouts(self):
        for service in ["analyticsAI","youtubeData"]:
            client=Mock();function=load_function(service+"/__init__.py","create_mongodb_client",{"os":os,"pymongo":types.SimpleNamespace(MongoClient=client)})
            with patch.dict(os.environ,{},clear=True):
                with self.assertRaises(RuntimeError):function()
            client.assert_not_called()
            with patch.dict(os.environ,{"YOUSIGHTS_MONGODB_URI":"mongodb://localhost/synthetic"},clear=True):function()
            self.assertEqual(client.call_args.args,("mongodb://localhost/synthetic",))
            self.assertEqual(client.call_args.kwargs["socketTimeoutMS"],15000)
    def test_refresh_body_and_timeout(self):
        response=Mock(content=b'{"access_token":"synthetic"}');requests=types.SimpleNamespace(post=Mock(return_value=response))
        function=load_function("eventsAPI/meetup.py","get_new_access_token",{"requests":requests,"json":json,"get_api_credentials":lambda:{"client_id":"id","client_secret":"secret","refresh_token":"token"}})
        self.assertEqual(function(),"synthetic")
        args,kwargs=requests.post.call_args;self.assertNotIn("?",args[0]);self.assertEqual(kwargs["data"]["client_secret"],"secret");self.assertEqual(kwargs["timeout"],(5,30))
    def test_deploy_never_shells_or_logs_key(self):
        spec=importlib.util.spec_from_file_location("safe_deploy",ROOT/"deploy_apps.py");module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        marker='synthetic-key; $(touch should-not-exist)';runner=Mock(return_value=types.SimpleNamespace(returncode=0));output=io.StringIO()
        with patch.object(module.subprocess,"run",runner),contextlib.redirect_stdout(output):module.execute_command(["ibmcloud","login","--apikey",marker])
        self.assertEqual(runner.call_args.args[0][-1],marker);self.assertNotIn("shell",runner.call_args.kwargs);self.assertNotIn(marker,output.getvalue())
    def test_api_models_work_under_maintained_restx(self):
        for service in ["eventsAPI","youtubeData","analyticsAI"]:
            app=Flask(service);api=Api(app).namespace("api/v1.0")
            spec=importlib.util.spec_from_file_location("models_"+service,ROOT/service/"api_models.py");module=importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules,{"__init__":types.SimpleNamespace(api=api)}):spec.loader.exec_module(module)
            self.assertTrue(api.models)
            self.assertEqual(app.test_client().get("/swagger.json").status_code,200)
    def test_frontend_maps_has_no_committed_key(self):
        source=(ROOT/"yousights-fe/server.py").read_text();namespace={"app":Flask("maps"),"os":os}
        from flask import redirect
        from urllib.parse import urlencode
        namespace.update(redirect=redirect,urlencode=urlencode)
        function=load_function("yousights-fe/server.py","maps_script",namespace)
        with namespace["app"].test_request_context("/maps.js"):
            with patch.dict(os.environ,{},clear=True):self.assertIsInstance(function(),tuple)
            with patch.dict(os.environ,{"YOUSIGHTS_MAPS_BROWSER_KEY":"synthetic-key"},clear=True):
                response=function();self.assertEqual(response.status_code,302);self.assertIn("key=synthetic-key",response.location)
        self.assertIn('src="/maps.js"',(ROOT/"yousights-fe/static/index.html").read_text())
    def test_examples_are_valid_and_secretless(self):
        for service in ["eventsAPI","youtubeData"]:json.loads((ROOT/service/"config/credentials.example.json").read_text())
        for item in json.loads((ROOT/"youtubeData/config/credentials.example.json").read_text())["credentials"].values():self.assertFalse(item["api_key"])
