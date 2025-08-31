"""
Sentiment Analysis Dialog for ScrapQT
Handles API key input and sentiment analysis confirmation
"""

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QComboBox, QTextEdit,
                           QCheckBox, QGroupBox, QProgressBar, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from typing import Optional, Dict, List
import grpc
from config_manager import ConfigManager
from src.scrapqt import services_pb2, services_pb2_grpc


class SentimentAnalysisWorker(QThread):
    """Background worker for sentiment analysis"""
    
    progress_update = pyqtSignal(str)  # status message
    batch_progress = pyqtSignal(int, int, int)  # current_batch, total_batches, items_processed
    analysis_completed = pyqtSignal(bool, int, str)  # success, items_analyzed, message
    
    def __init__(self, api_key: str, batch_size: int = 10, batch_delay: float = 1.0):
        super().__init__()
        self.api_key = api_key
        self.batch_size = batch_size
        self.batch_delay = batch_delay
        self.original_api_key = None
    
    def run(self):
        """Run sentiment analysis in background with batch processing"""
        import time
        
        try:
            self.progress_update.emit("Preparing API key...")
            
            # Temporarily set the API key in environment
            import os
            self.original_api_key = os.environ.get('GEMINI_API_KEY')
            
            # Handle saved keys
            actual_api_key = self.api_key
            if self.api_key.startswith("SAVED_KEY:"):
                key_id = self.api_key.replace("SAVED_KEY:", "")
                from config_manager import ConfigManager
                config_manager = ConfigManager()
                
                # Get the key from persistent storage
                saved_key = config_manager.get_session_api_key(key_id)
                if saved_key:
                    actual_api_key = saved_key
                    self.progress_update.emit("Using saved API key...")
                else:
                    self.progress_update.emit("Error: Unable to retrieve saved API key")
                    self.analysis_completed.emit(False, 0, 
                        "Unable to retrieve saved API key. The key may have been corrupted or removed.")
                    return
            
            # Set the API key temporarily
            os.environ['GEMINI_API_KEY'] = actual_api_key
            
            self.progress_update.emit("Loading products from database...")
            
            # Get products from database
            from database_manager import DatabaseManager
            db = DatabaseManager()
            products = db.get_all_products()
            
            if not products:
                self.analysis_completed.emit(False, 0, "No products found in database")
                return
            
            # Filter products that need sentiment analysis (don't have sentiment_score)
            products_to_analyze = [p for p in products if p.get('sentiment_score') is None]
            
            if not products_to_analyze:
                self.analysis_completed.emit(True, 0, "All products already have sentiment scores")
                return
            
            total_products = len(products_to_analyze)
            total_batches = (total_products + self.batch_size - 1) // self.batch_size  # Ceiling division
            
            self.progress_update.emit(f"Starting batch analysis of {total_products} products...")
            self.batch_progress.emit(0, total_batches, 0)
            
            # Connect to sentiment service
            with grpc.insecure_channel('localhost:60001') as channel:
                sentiment_stub = services_pb2_grpc.SentimentStub(channel)
                
                items_analyzed = 0
                failed_items = 0
                
                for batch_num in range(total_batches):
                    start_idx = batch_num * self.batch_size
                    end_idx = min(start_idx + self.batch_size, total_products)
                    batch_products = products_to_analyze[start_idx:end_idx]
                    
                    self.progress_update.emit(f"Processing batch {batch_num + 1}/{total_batches} ({len(batch_products)} products)...")
                    
                    # Process each product in the batch
                    for product in batch_products:
                        try:
                            # Create sentiment analysis request
                            text_to_analyze = f"{product.get('title', '')} {product.get('description', '')}"
                            request = services_pb2.SentimentRequest(text=text_to_analyze)
                            
                            # Analyze sentiment
                            response = sentiment_stub.Analyze(request)
                            
                            # Update database with sentiment score
                            # Convert score from 1-10 scale to -1 to 1 scale
                            normalized_score = (response.score - 5.5) / 4.5
                            
                            # Update the product in database
                            db.update_product_sentiment(product['id'], normalized_score)
                            items_analyzed += 1
                            
                        except Exception as e:
                            self.progress_update.emit(f"Failed to analyze product {product.get('title', 'Unknown')}: {str(e)}")
                            failed_items += 1
                    
                    # Update progress
                    progress_percentage = ((batch_num + 1) / total_batches) * 100
                    self.batch_progress.emit(batch_num + 1, total_batches, items_analyzed)
                    
                    # Delay between batches (except for the last batch)
                    if batch_num < total_batches - 1 and self.batch_delay > 0:
                        self.progress_update.emit(f"Waiting {self.batch_delay} seconds before next batch...")
                        time.sleep(self.batch_delay)
                
                success_msg = f"Analysis completed! Analyzed {items_analyzed} products"
                if failed_items > 0:
                    success_msg += f" ({failed_items} failed)"
                
                self.analysis_completed.emit(True, items_analyzed, success_msg)
                
        except grpc.RpcError as e:
            error_msg = f"gRPC Error: {e.details()}"
            self.progress_update.emit(f"Error: {error_msg}")
            self.analysis_completed.emit(False, 0, error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.progress_update.emit(f"Error: {error_msg}")
            self.analysis_completed.emit(False, 0, error_msg)
        
        finally:
            # Restore original API key
            import os
            if self.original_api_key is not None:
                os.environ['GEMINI_API_KEY'] = self.original_api_key
            elif 'GEMINI_API_KEY' in os.environ:
                del os.environ['GEMINI_API_KEY']


class SentimentAnalysisDialog(QDialog):
    """Dialog for configuring and starting sentiment analysis"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.worker = None
        
        self.setWindowTitle("Sentiment Analysis")
        self.setWindowIcon(QtGui.QIcon(":/resource/Stats.png"))
        self.setModal(True)
        
        # Set more appropriate dialog sizing to prevent geometry warnings
        self.setMinimumSize(450, 500)  # Set reasonable minimum size
        self.resize(550, 600)  # Larger initial size to accommodate content
        
        # Make dialog resizable with reasonable constraints
        self.setWindowFlags(
            QtCore.Qt.Dialog | 
            QtCore.Qt.WindowSystemMenuHint | 
            QtCore.Qt.WindowTitleHint | 
            QtCore.Qt.WindowCloseButtonHint
        )
        
        # Setup UI
        self.setup_ui()
        self.load_saved_keys()
        
        # Connect signals
        self.api_key_combo.currentTextChanged.connect(self.on_api_key_selection_changed)
        self.save_key_checkbox.toggled.connect(self.on_save_key_toggled)
        self.test_key_button.clicked.connect(self.test_api_key)
        self.save_key_button.clicked.connect(self.save_current_api_key)
        self.clear_all_keys_button.clicked.connect(self.clear_all_api_keys)
        self.start_analysis_button.clicked.connect(self.start_analysis)
        self.cancel_button.clicked.connect(self.reject)
        
    def setup_ui(self):
        """Setup the dialog UI"""
        # Set layout margins to be more compact
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)  # Reduce margins
        layout.setSpacing(10)  # Consistent spacing
        
        # Title
        title_label = QLabel("Sentiment Analysis Configuration")
        title_label.setStyleSheet("font: bold 14px; color: #2c3e50; margin-bottom: 8px;")
        layout.addWidget(title_label)
        
        # Description - make it more compact
        desc_label = QLabel(
            "Analyze the sentiment of all products using Google's Gemini AI. "
            "API keys are securely stored locally and encrypted for convenience."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #555; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(desc_label)
        
        # API Key Configuration Group
        api_group = QGroupBox("Gemini API Key Configuration")
        api_layout = QVBoxLayout(api_group)
        
        # Saved keys combo
        self.api_key_combo = QComboBox()
        self.api_key_combo.setEditable(True)
        self.api_key_combo.setPlaceholderText("Enter your Gemini API key or select from saved keys")
        self.api_key_combo.lineEdit().setEchoMode(QLineEdit.Password)
        api_layout.addWidget(QLabel("API Key:"))
        api_layout.addWidget(self.api_key_combo)
        
        # API key options
        key_options_layout = QHBoxLayout()
        
        self.save_key_checkbox = QCheckBox("Save this API key for future use")
        self.save_key_checkbox.setChecked(True)
        key_options_layout.addWidget(self.save_key_checkbox)
        
        key_options_layout.addStretch()
        
        self.test_key_button = QPushButton("Test Key")
        self.test_key_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        key_options_layout.addWidget(self.test_key_button)
        
        api_layout.addLayout(key_options_layout)
        
        # Key name input (for saving)
        self.key_name_layout = QHBoxLayout()
        self.key_name_input = QLineEdit()
        self.key_name_input.setPlaceholderText("Optional: Name for this API key")
        self.key_name_layout.addWidget(QLabel("Key Name:"))
        self.key_name_layout.addWidget(self.key_name_input)
        
        # Save Key button
        self.save_key_button = QPushButton("Save Key")
        self.save_key_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.key_name_layout.addWidget(self.save_key_button)
        
        api_layout.addLayout(self.key_name_layout)
        
        # Key management buttons
        key_management_layout = QHBoxLayout()
        key_management_layout.addStretch()  # Push buttons to the right
        
        self.clear_all_keys_button = QPushButton("Clear All Keys")
        self.clear_all_keys_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        key_management_layout.addWidget(self.clear_all_keys_button)
        
        api_layout.addLayout(key_management_layout)
        
        layout.addWidget(api_group)
        
        # Analysis Configuration Group
        config_group = QGroupBox("Analysis Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # Batch size configuration
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("Batch Size:"))
        
        self.batch_size_spin = QtWidgets.QSpinBox()
        self.batch_size_spin.setRange(1, 100)
        self.batch_size_spin.setValue(10)  # Default batch size
        self.batch_size_spin.setToolTip("Number of products to analyze in each batch. Smaller batches reduce API rate limit issues.")
        batch_layout.addWidget(self.batch_size_spin)
        
        batch_layout.addWidget(QLabel("products per batch"))
        batch_layout.addStretch()
        
        config_layout.addLayout(batch_layout)
        
        # Batch delay configuration
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Delay between batches:"))
        
        self.batch_delay_spin = QtWidgets.QDoubleSpinBox()
        self.batch_delay_spin.setRange(0.0, 10.0)
        self.batch_delay_spin.setValue(1.0)  # Default 1 second delay
        self.batch_delay_spin.setSingleStep(0.5)
        self.batch_delay_spin.setSuffix(" seconds")
        self.batch_delay_spin.setToolTip("Delay between batches to avoid overwhelming the API.")
        delay_layout.addWidget(self.batch_delay_spin)
        
        delay_layout.addStretch()
        config_layout.addLayout(delay_layout)
        
        layout.addWidget(config_group)
        
        # Progress section (initially hidden)
        self.progress_group = QGroupBox("Analysis Progress")
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_label = QLabel("Ready to start analysis...")
        progress_layout.addWidget(self.progress_label)
        
        # Overall progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)  # Percentage-based progress
        self.progress_bar.hide()
        progress_layout.addWidget(self.progress_bar)
        
        # Batch progress label
        self.batch_progress_label = QLabel("")
        self.batch_progress_label.setStyleSheet("color: #666; font-size: 11px;")
        self.batch_progress_label.hide()
        progress_layout.addWidget(self.batch_progress_label)
        
        self.progress_group.hide()
        layout.addWidget(self.progress_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        self.start_analysis_button = QPushButton("Start Analysis")
        self.start_analysis_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        button_layout.addWidget(self.start_analysis_button)
        
        layout.addLayout(button_layout)
    
    def load_saved_keys(self):
        """Load saved API keys into the combo box"""
        self.api_key_combo.clear()
        
        # Add empty option
        self.api_key_combo.addItem("Enter new API key...", "")
        
        # Add saved keys (all keys are now persistently available)
        saved_keys = self.config_manager.get_saved_api_keys()
        for key_info in saved_keys:
            display_text = f"{key_info['name']} ({key_info['key_hash']})"
            self.api_key_combo.addItem(display_text, key_info['key_id'])
        
        # Select last used key if available
        last_used_id = self.config_manager.get_last_used_key_id()
        if last_used_id:
            for i in range(self.api_key_combo.count()):
                if self.api_key_combo.itemData(i) == last_used_id:
                    self.api_key_combo.setCurrentIndex(i)
                    break
    
    def on_api_key_selection_changed(self):
        """Handle API key selection change"""
        current_data = self.api_key_combo.currentData()
        if current_data:  # Saved key selected
            self.save_key_checkbox.setChecked(False)
            self.save_key_checkbox.setEnabled(False)
            self.key_name_input.setEnabled(False)
            self.save_key_button.setEnabled(False)
            self.api_key_combo.lineEdit().setEchoMode(QLineEdit.Normal)
            self.api_key_combo.lineEdit().setText("(Using saved API key)")
        else:  # New key entry
            self.save_key_checkbox.setEnabled(True)
            self.key_name_input.setEnabled(True)
            self.save_key_button.setEnabled(True)
            self.api_key_combo.lineEdit().setEchoMode(QLineEdit.Password)
            if self.api_key_combo.lineEdit().text() == "(Using saved API key)":
                self.api_key_combo.lineEdit().setText("")
    
    def on_save_key_toggled(self, checked):
        """Handle save key checkbox toggle"""
        self.key_name_input.setEnabled(checked)
    
    def save_current_api_key(self):
        """Save the current API key"""
        api_key = self.api_key_combo.currentText().strip()
        
        if not api_key:
            QMessageBox.warning(self, "Warning", "Please enter an API key first.")
            return
        
        if api_key == "(Using saved API key)":
            QMessageBox.warning(self, "Warning", "Please enter a new API key to save.")
            return
        
        # Validate format
        if not self.config_manager.validate_api_key_format(api_key):
            reply = QMessageBox.question(
                self, "Invalid API Key Format",
                "The API key format appears to be invalid. Do you want to save it anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        try:
            key_name = self.key_name_input.text().strip()
            if not key_name:
                key_name = f"API Key {len(self.config_manager.get_saved_api_keys()) + 1}"
            
            key_id = self.config_manager.save_api_key(api_key, key_name)
            print(f"API key saved with ID: {key_id}")
            
            # Refresh the dropdown to show the newly saved key
            self.load_saved_keys()
            
            # Select the newly saved key
            for i in range(self.api_key_combo.count()):
                if self.api_key_combo.itemData(i) == key_id:
                    self.api_key_combo.setCurrentIndex(i)
                    break
            
            # Clear the key name input for next use
            self.key_name_input.clear()
            
            # Show success message
            QMessageBox.information(
                self, "Key Saved Successfully", 
                f"API key '{key_name}' has been saved successfully!\n\n"
                f"It will be available in the dropdown for future use, even after restarting the application."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save API key: {e}")
    
    def clear_all_api_keys(self):
        """Clear all saved API keys after confirmation."""
        saved_keys = self.config_manager.get_saved_api_keys()
        
        if not saved_keys:
            QMessageBox.information(self, "Info", "No API keys to clear.")
            return
        
        # Confirmation dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Clear All Keys", 
            f"Are you sure you want to delete all {len(saved_keys)} saved API keys?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.config_manager.clear_all_api_keys():
                    # Refresh the dropdown
                    self.load_saved_keys()
                    # Clear the current text
                    self.api_key_combo.setCurrentText("")
                    
                    QMessageBox.information(self, "Success", "All API keys have been cleared.")
                else:
                    QMessageBox.warning(self, "Error", "Failed to clear API keys. Please try again.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear API keys: {e}")
    
    def get_current_api_key(self) -> Optional[str]:
        """Get the current API key (either entered or from saved keys)"""
        current_data = self.api_key_combo.currentData()
        if current_data:  # Saved key
            # In a real implementation, you'd need to securely retrieve the actual key
            # For now, we'll assume the server handles the key lookup
            return f"SAVED_KEY:{current_data}"
        else:  # Manual entry
            return self.api_key_combo.currentText().strip()
    
    def test_api_key(self):
        """Test the current API key"""
        api_key = self.get_current_api_key()
        if not api_key:
            QMessageBox.warning(self, "Warning", "Please enter or select an API key first.")
            return
        
        # Validate format
        if not api_key.startswith("SAVED_KEY:") and not self.config_manager.validate_api_key_format(api_key):
            QMessageBox.warning(
                self, "Invalid API Key", 
                "The API key format appears to be invalid. Gemini API keys should start with 'AI' or 'sk-'."
            )
            return
        
        # For now, just show a format validation message
        QMessageBox.information(
            self, "API Key Test", 
            "API key format looks valid. The actual key will be tested during sentiment analysis."
        )
    
    def start_analysis(self):
        """Start the sentiment analysis process"""
        api_key = self.get_current_api_key()
        
        if not api_key:
            QMessageBox.warning(self, "Warning", "Please enter or select an API key first.")
            return
        
        # Validate and save key if requested
        if not api_key.startswith("SAVED_KEY:"):
            if not self.config_manager.validate_api_key_format(api_key):
                reply = QMessageBox.question(
                    self, "Invalid API Key Format",
                    "The API key format appears to be invalid. Do you want to continue anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            
            # Save key if requested
            if self.save_key_checkbox.isChecked():
                try:
                    key_name = self.key_name_input.text().strip()
                    key_id = self.config_manager.save_api_key(api_key, key_name)
                    print(f"API key saved with ID: {key_id}")
                    
                    # Refresh the dropdown to show the newly saved key
                    self.load_saved_keys()
                    
                    # Select the newly saved key
                    for i in range(self.api_key_combo.count()):
                        if self.api_key_combo.itemData(i) == key_id:
                            self.api_key_combo.setCurrentIndex(i)
                            break
                    
                    # Show success message
                    QMessageBox.information(
                        self, "Key Saved", 
                        f"API key '{key_name}' has been saved successfully!\n\n"
                        f"It will be available in future sessions."
                    )
                    
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to save API key: {e}")
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self, "Confirm Sentiment Analysis",
            "This will analyze the sentiment of all products in your database using the Gemini AI service. "
            "This may take some time and will use API credits. Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Start analysis
        self.start_analysis_button.setEnabled(False)
        self.progress_group.show()
        self.progress_bar.show()
        self.batch_progress_label.show()
        
        # Instead of adjustSize() which can cause geometry issues,
        # ensure dialog is large enough for the progress group
        current_size = self.size()
        min_height = 650  # Ensure enough height for progress
        if current_size.height() < min_height:
            self.resize(current_size.width(), min_height)
        
        # Start worker thread with batch configuration
        batch_size = self.batch_size_spin.value()
        batch_delay = self.batch_delay_spin.value()
        
        self.worker = SentimentAnalysisWorker(api_key, batch_size, batch_delay)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.batch_progress.connect(self.update_batch_progress)
        self.worker.analysis_completed.connect(self.analysis_finished)
        self.worker.start()
    
    def update_progress(self, message: str):
        """Update progress display"""
        self.progress_label.setText(message)
    
    def update_batch_progress(self, current_batch: int, total_batches: int, items_processed: int):
        """Update batch progress display"""
        if total_batches > 0:
            progress_percentage = (current_batch / total_batches) * 100
            self.progress_bar.setValue(int(progress_percentage))
            self.batch_progress_label.setText(f"Batch {current_batch}/{total_batches} - {items_processed} items processed")
    
    def analysis_finished(self, success: bool, items_analyzed: int, message: str):
        """Handle analysis completion"""
        self.progress_bar.hide()
        self.start_analysis_button.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self, "Analysis Complete",
                f"Sentiment analysis completed successfully!\n\n"
                f"Items analyzed: {items_analyzed}\n"
                f"Results have been saved to the database."
            )
            
            # Mark API key as used if it was a saved key
            current_data = self.api_key_combo.currentData()
            if current_data:
                self.config_manager.mark_api_key_used(current_data)
            
            self.accept()  # Close dialog with success
        else:
            QMessageBox.critical(
                self, "Analysis Failed",
                f"Sentiment analysis failed:\n\n{message}\n\n"
                f"Please check your API key and try again."
            )
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "Analysis in Progress",
                "Sentiment analysis is currently running. Do you want to cancel it?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.worker:
                    self.worker.terminate()
                    self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
