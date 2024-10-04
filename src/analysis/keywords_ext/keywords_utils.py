import logging
logger = logging.getLogger(__name__)


def keyword_selection(keyword_extraction_output, audio_analysis_output):
    try:
        keywords = keyword_extraction_output.lower().split(', ') if keyword_extraction_output else []
        audio_words = audio_analysis_output.lower().split(', ') if audio_analysis_output else []

        # Initialize the final output list with the first two words from audio analysis output
        final_output = audio_words[:2]

        # Add remaining words from keywords to ensure final_output has at least 4 unique words
        for word in keywords:
            if len(final_output) == 4:
                break
            if word not in final_output:
                final_output.append(word)
        
        # If final_output is still less than 4 words, fill in from audio_words
        for word in audio_words:
            if len(final_output) == 4:
                break
            if word not in final_output:
                final_output.append(word)
        
        # Ensure the output has exactly 4 words
        return final_output[:4]

    except Exception as e:
        logger.error(f"Error in keyword_selection: {e}")
        return ['None'] * 4


def aggregate_keywords(audio_keywords, video_keywords, video_uuid="<video_uuid>"):
    if not video_keywords and not audio_keywords:
        logger.warning(f"No keywords extracted from both video and audio for video: {video_uuid}.")
        aggregated_keywords = None
    elif not video_keywords:
        logger.warning(f"No keywords extracted from video for video: {video_uuid}.")
        aggregated_keywords = audio_keywords.strip(' ,')
    elif not audio_keywords:
        logger.warning(f"No keywords extracted from audio for video: {video_uuid}.")
        aggregated_keywords = video_keywords.strip(' ,')
    else:
        aggregated_keywords = f"{audio_keywords.strip(' ,')}, {video_keywords.strip(' ,')}"

    aggregated_keywords_list = [word.lower() for word in aggregated_keywords.split(', ') if word.strip()]
    aggregated_keywords_list = list(set(aggregated_keywords_list))

    extracted_4_keywords = keyword_selection(video_keywords, audio_keywords)
    # Combine keywords without duplicates
    keywords = extracted_4_keywords + [word for word in aggregated_keywords_list if
                                       word not in extracted_4_keywords]
    return keywords
