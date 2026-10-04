# For YouTube video transcript analysis


import io
from sources import youtube_transcript_text_analysis, youtube_text_processing


class GeneratingPeriodsTranscriptsException(Exception):
    pass


# Generate separate transcript text for separate periods
def generate_periods_transcript_text(original_transcript, periods_count):
    # Bound upstream/DB transcript size before scanning it once per period.
    youtube_text_processing.get_trans_str(original_transcript)
    original_transcript_count = len(original_transcript)

    # if original_transcript is empty, raise an exception
    if original_transcript_count == 0:
        raise GeneratingPeriodsTranscriptsException("original_transcript is an empty list.")

    last_transcript_item = original_transcript[original_transcript_count - 1]
    video_duration = last_transcript_item["start"] + last_transcript_item["duration"]

    # if the duration covered by original_transcript is 0, raise an exception
    if video_duration == 0:
        raise GeneratingPeriodsTranscriptsException("The duration covered by original_transcript is 0.")

    # divide original_transcript into periods_count periods, and build the transcript text for each of these periods

    ret_info = []

    period_duration = video_duration / periods_count
    this_period_start = 0
    this_period_end = period_duration

    i = 0
    while i < periods_count:
        this_period_text_builder = io.StringIO("")

        whether_have_written_something = False

        j = 0
        while j < original_transcript_count:
            this_transcript_item = original_transcript[j]
            this_transcript_item_start = this_transcript_item["start"]

            if (this_transcript_item_start >= this_period_start) and (this_transcript_item_start <= this_period_end):
                if whether_have_written_something is False:
                    whether_have_written_something = True
                else:
                    this_period_text_builder.write("\n")

                this_period_text_builder.write(this_transcript_item["text"])

            j = j + 1

        this_period_text = this_period_text_builder.getvalue()
        this_period_text_builder.close()

        this_period_info = {"text": this_period_text, "start": this_period_start, "end": this_period_end}

        ret_info.append(this_period_info)

        this_period_start = this_period_end
        this_period_end = this_period_start + period_duration

        i = i + 1

    return ret_info


class GeneratingTableOfContentsException(Exception):
    pass


# Generate table of contents for a video
def generate_table_of_contents(original_transcript):
    try:
        periods_transcript_text = generate_periods_transcript_text(original_transcript, 10)
    except GeneratingPeriodsTranscriptsException:
        raise GeneratingTableOfContentsException("The separate transcripts cannot be generated.")

    try:
        table_of_contents = []

        count = len(periods_transcript_text)
        i = 0
        while i < count:
            this_transcript_text_item = periods_transcript_text[i]
            this_table_item = {"start": this_transcript_text_item["start"], "end": this_transcript_text_item["end"]}

            # call another function to actually generate the text in the table of contents for this_transcript_text_item
            this_content_text = youtube_transcript_text_analysis.generate_table_of_contents_text(this_transcript_text_item["text"])

            this_table_item["content"] = this_content_text
            table_of_contents.append(this_table_item)
            i = i + 1
    except Exception:
        raise GeneratingTableOfContentsException("An exception occurs when trying to generate the table of contents.")

    return table_of_contents
