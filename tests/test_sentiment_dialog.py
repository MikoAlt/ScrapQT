#!/usr/bin/env python3

import sys
sys.path.append('.')

from PyQt5.QtWidgets import QApplication
from sentiment_dialog import SentimentAnalysisDialog

def test_sentiment_dialog():
    """Test the sentiment analysis dialog independently"""
    app = QApplication(sys.argv)
    
    # Create and show the dialog
    dialog = SentimentAnalysisDialog()
    
    # Show dialog
    result = dialog.exec_()
    
    if result == dialog.Accepted:
        print("Dialog completed successfully!")
    else:
        print("Dialog was cancelled or closed")
    
    app.quit()

if __name__ == "__main__":
    test_sentiment_dialog()
