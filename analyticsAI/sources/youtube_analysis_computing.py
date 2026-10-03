from sources.youtube_similarity import Similarity
from sources import youtube_text_processing as text_processing
from sources import youtube_sentiment_fast
from sources import youtube_transcript_analysis
from sources import youtube_entities
from __init__ import entity_type, entity_max_count
import corpus
import logging
import traceback
from sources.nlp_limits import NLPLimitError

logging.getLogger(__name__)


def analysis_computing(query, source, api_ret):
    try:
        video_insights = {"video_statistic_data": list(), "video_count": api_ret["video_results_count"]}
    except Exception as error:
        logging.error(f"Error while Analysing Youtube data: {error}")
        logging.error(traceback.format_exc())

        # video_insights.append("debug")

    if source == "cached":
        keywords_corpus = corpus.get_keywords_corpus(query)
        # Transcript list for calculating the similarity
        transcripts_list = list()

        # Add book keywords into the list as the first parameter
        transcripts_list.append(keywords_corpus)

    for video_detail in api_ret["video_results"]:
        # if video_detail['video_id'] == 'rfscVS0vtbw': continue
        try:
            en_transcript = text_processing.get_trans_str(video_detail["data"]["en_transcript"])
        except NLPLimitError:
            raise
        except Exception as error:
            logging.error(f"Error while converting raw transcript to string: {error}")
            logging.error(traceback.format_exc())

        if source == "cached":
            try:
                # en_transcript_keywords = text_processing.text_preprocessed_key(en_transcript)
                en_transcript_keywords = text_processing.get_weighted_keywords(en_transcript)
            except NLPLimitError:
                raise
            except Exception as error:
                logging.error(f"Error while generating the keywords for transcript: {error}")
                logging.error(traceback.format_exc())

            transcripts_list.append(en_transcript_keywords)
        # video_sentiment = sentiment_wrapper(video_detail["data"]["some_comments"]["comment_results"], video_detail["data"]["some_comments"]["comment_results_more_info"])
        try:
            video_sentiment = youtube_sentiment_fast.sentiment_fast(video_detail["data"]["some_comments"]["comment_results"], video_detail["data"]["some_comments"]["comment_results_more_info"])
        except Exception as error:
            logging.error(f"Error while fetching video sentiment: {error}")
            logging.error(traceback.format_exc())

        video_analysis_data = {
            "title": video_detail["data"]["title"],
            "likeCount": video_detail["data"]["likeCount"],
            "dislikeCount": video_detail["data"]["dislikeCount"],
            "viewCount": video_detail["data"]["viewCount"],
            "en_transcript": {
                # This code will be improved later
                "relevant_book": "url",
                # "keywords_trans": en_transcript_keywords,
            },
            "comments": {"sentiment": video_sentiment},
        }

        if source == "cached":
            is_failure = False
            try:
                table_of_contents = youtube_transcript_analysis.generate_table_of_contents(video_detail["data"]["en_transcript"])
            except youtube_transcript_analysis.GeneratingTableOfContentsException as error:
                logging.error(f"Error while trying to compute the table of content: {error}")
                logging.error(traceback.format_exc())
                is_failure = True

            if is_failure is False:
                video_analysis_data["en_transcript"]["table_of_contents"] = table_of_contents

            try:
                video_analysis_data["en_transcript"]["freq_trans"] = text_processing.get_freq(en_transcript, keywords_corpus)
            except Exception as error:
                logging.error(f"Error while fetching the word frequency (cached data): {error}")
                logging.error(traceback.format_exc())

            try:
                video_analysis_data["en_transcript"]["entities"] = youtube_entities.get_entity(en_transcript, entity_type, entity_max_count)
            except Exception as error:
                logging.error(f"Error while fetching the video entities: {error}")
                logging.error(traceback.format_exc())

        else:
            try:
                video_analysis_data["en_transcript"]["freq_trans"] = text_processing.get_freq(en_transcript)
            except Exception as error:
                logging.error(f"Error while fetching the word frequency (live data): {error}")
                logging.error(traceback.format_exc())

        video_analysis = {"video_id": video_detail["video_id"], "data": video_analysis_data}

        video_insights["video_statistic_data"].append(video_analysis)
    if source == "cached":
        try:
            transcripts_cosine_similarity = Similarity().cos_similarity(transcripts_list)

            similarity_max = max(transcripts_cosine_similarity)
            similarity_min = min(transcripts_cosine_similarity)

            if similarity_max == similarity_min:
                for video in video_insights["video_statistic_data"]:
                    video["data"]["en_transcript"]["trans_similarity_nor"] = 5
                    video["data"]["en_transcript"]["trans_similarity"] = similarity_max
            else:
                for index, video in enumerate(video_insights["video_statistic_data"]):
                    video["data"]["en_transcript"]["trans_similarity"] = transcripts_cosine_similarity[index]
                    video["data"]["en_transcript"]["trans_similarity_nor"] = round((video["data"]["en_transcript"]["trans_similarity"] - similarity_min) / (similarity_max - similarity_min) * 10)
        except Exception as error:
            logging.error(f"Error while fetching the normalized similarity: {error}")
            logging.error(traceback.format_exc())

    return video_insights
