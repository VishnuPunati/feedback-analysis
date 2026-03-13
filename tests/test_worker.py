def test_sentiment_logic():
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    analyzer = SentimentIntensityAnalyzer()

    result = analyzer.polarity_scores("This product is amazing")

    assert result["compound"] > 0