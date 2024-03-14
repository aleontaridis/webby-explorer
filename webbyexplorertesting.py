from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import os
import json

class LineEdit(QLineEdit):
    def __init__(self, parent=None):
        super(LineEdit, self).__init__(parent)
        self.setStyleSheet("""
            border-radius: 3px;
            background: lightgray;
            color: #333;
        """)

        # Create a syntax highlighter
        self.highlighter = Highlighter(self)

        # Set up a validator to disallow spaces
        self.setValidator(QRegExpValidator(QRegExp("[^\\s]*"), self))

    def setText(self, text):
        super(LineEdit, self).setText(text)
        self.highlighter.rehighlight()

class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)
        self.parent = parent

    def highlightBlock(self, text):
        format_http = QTextCharFormat()
        format_http.setForeground(QBrush(QColor("#414141")))  # Your desired color for "http://"

        format_https = QTextCharFormat()
        format_https.setForeground(QBrush(QColor("#414141")))  # Your desired color for "https://"

        http_pattern = QRegExp("http://")
        https_pattern = QRegExp("https://")

        index_http = http_pattern.indexIn(text)
        while index_http >= 0:
            length = http_pattern.matchedLength()
            self.setFormat(index_http, length, format_http)
            index_http = http_pattern.indexIn(text, index_http + length)

        index_https = https_pattern.indexIn(text)
        while index_https >= 0:
            length = https_pattern.matchedLength()
            self.setFormat(index_https, length, format_https)
            index_https = https_pattern.indexIn(text, index_https + length)

class BrowserView(QWebEngineView):
    def __init__(self, parent=None):
        super(BrowserView, self).__init__(parent)

    def createWindow(self, type):
        new_view = BrowserView(self)
        window = MainWindow.browser_window(new_view)
        window.show()
        return new_view

class BrowserView(QWebEngineView):
    def __init__(self, parent=None):
        super(BrowserView, self).__init__(parent)

    def createWindow(self, type):
        new_view = BrowserView(self)
        window = MainWindow.browser_window(new_view)
        window.show()
        return new_view

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.setCentralWidget(self.tabs)

        navbar = QToolBar()
        self.addToolBar(navbar)

        back_btn = QAction('⮜', self)
        back_btn.setStatusTip('Return to the previous page.')
        back_btn.triggered.connect(lambda: self.current_browser().back())
        navbar.addAction(back_btn)

        forward_btn = QAction('⮞', self)
        forward_btn.triggered.connect(lambda: self.current_browser().forward())
        forward_btn.setStatusTip('Go forward to the next page.')
        navbar.addAction(forward_btn)

        reload_btn = QAction('⟳', self)
        reload_btn.triggered.connect(lambda: self.current_browser().reload())
        reload_btn.setStatusTip('Reload the current page.')
        navbar.addAction(reload_btn)

        stop_btn = QAction('✕', self)
        stop_btn.setStatusTip('Stop loading the current page.')
        stop_btn.triggered.connect(lambda: self.current_browser().stop())
        navbar.addAction(stop_btn)

        home_btn = QAction('🏠', self)
        home_btn.setStatusTip('Navigate to home.')
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)
        self.tabs.currentChanged.connect(lambda _: self.update_url(self.current_browser().url()))
        self.url_bar.setPlaceholderText("Search or type a URL here...")

        settings_btn = QAction('⚙️', self)
        settings_btn.setStatusTip('Open settings.')
        # settings_btn.triggered.connect(self.show_settings)
        navbar.addAction(settings_btn)

        self.shortcutBackward = QShortcut(QKeySequence("Alt+Left"), self)
        self.shortcutBackward.activated.connect(lambda: self.current_browser().back())

        self.shortcutForward = QShortcut(QKeySequence("Alt+Right"), self)
        self.shortcutForward.activated.connect(lambda: self.current_browser().forward())

        self.shortcutReload = QShortcut(QKeySequence("F5"), self)
        self.shortcutReload.activated.connect(lambda: self.current_browser().reload())

        self.shortcutStopLoading = QShortcut(QKeySequence("Esc"), self)
        self.shortcutStopLoading.activated.connect(lambda: self.current_browser().stop())

        # Adding the tab shortcuts
        self.shortcutNewTab = QShortcut(QKeySequence("Ctrl+T"), self)
        self.shortcutNewTab.activated.connect(self.add_new_tab)

        self.shortcutCloseTab = QShortcut(QKeySequence("Ctrl+W"), self)
        self.shortcutCloseTab.activated.connect(lambda: self.close_current_tab(self.tabs.currentIndex()))

        self.shortcutNextTab = QShortcut(QKeySequence("Ctrl+Tab"), self)
        self.shortcutNextTab.activated.connect(lambda: self.tabs.setCurrentIndex((self.tabs.currentIndex() + 1) % self.tabs.count()))

        self.shortcutPrevTab = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        self.shortcutPrevTab.activated.connect(lambda: self.tabs.setCurrentIndex((self.tabs.currentIndex() - 1) % self.tabs.count()))

        # Adding the address bar shortcuts

        self.shortcutCompleteURL = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.shortcutCompleteURL.activated.connect(lambda: self.url_bar.setText("http://www." + self.url_bar.text() + ".com"))

        self.shortcutOpenAddressNewTab = QShortcut(QKeySequence("Alt+Return"), self)
        self.shortcutOpenAddressNewTab.activated.connect(lambda: self.add_new_tab(QUrl(self.url_bar.text())))

        # Adding the page zoom shortcuts
        self.shortcutZoomIn = QShortcut(QKeySequence("Ctrl" + "+"), self)
        self.shortcutZoomIn.activated.connect(lambda: self.current_browser().setZoomFactor(self.current_browser().zoomFactor() + 0.1))

        self.shortcutZoomOut = QShortcut(QKeySequence("Ctrl+-"), self)
        self.shortcutZoomOut.activated.connect(lambda: self.current_browser().setZoomFactor(self.current_browser().zoomFactor() - 0.1))

        self.shortcutResetZoom = QShortcut(QKeySequence("Ctrl+0"), self)
        self.shortcutResetZoom.activated.connect(lambda: self.current_browser().setZoomFactor(1.0))

        # Adding miscellaneous shortcuts

        self.shortcutOpenDevTools = QShortcut(QKeySequence("Ctrl+Shift+I"), self)
        self.shortcutOpenDevTools.activated.connect(lambda: self.current_browser().page().inspectElement(QPoint(0, 0)))

        self.shortcutFindOnPage = QShortcut(QKeySequence("Ctrl+F"), self)
        self.shortcutFindOnPage.activated.connect(lambda: self.current_browser().findText("", QWebEnginePage.FindFlags()))

        self.shortcutPrintPage = QShortcut(QKeySequence("Ctrl+P"), self)
        self.shortcutPrintPage.activated.connect(lambda: self.current_browser().page().printToPdf())

        # Adding mouse shortcuts

        self.shortcutCloseTabMiddleClick = QShortcut(QKeySequence("MiddleClick"), self)
        self.shortcutCloseTabMiddleClick.activated.connect(lambda: self.close_current_tab(self.tabs.currentIndex()))

        font = QFont()
        font.setPointSize(14)
        back_btn.setFont(font)
        forward_btn.setFont(font)
        stop_btn.setFont(font)
        settings_btn.setFont(font)
        home_btn.setFont(font)
        reload_btn.setFont(font)
        font3 = QFont()
        font3.setPointSize(12)
        navbar.setFont(font3)
        font4 = QFont()
        font4.setPointSize(10)
        self.tabs.setFont(font4)

        script_dir = os.path.dirname(os.path.realpath(__file__))
        folder_name = "home"
        local_file_url = QUrl.fromLocalFile(os.path.join(script_dir, folder_name, "home.html"))
        self.add_new_tab(QUrl(local_file_url), 'Homepage')

        browser = BrowserView()
        browser.page().featurePermissionRequested.connect(self.feature_permission_requested)

        icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'icon.ico')
        self.showMaximized()
        self.setWindowTitle("Webby Explorer")
        self.setWindowIcon(QIcon(icon_path))
         
        style_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'styles.css')
        with open(style_path, "r") as style:
            self.setStyleSheet(style.read())

    def add_new_tab(self, qurl=None, label="Blank"):

        script_dir = os.path.dirname(os.path.realpath(__file__))
        folder_name = "home"
        local_file_url = QUrl.fromLocalFile(os.path.join(script_dir, folder_name, "home.html"))

        if qurl is None:
            qurl = QUrl(local_file_url)
            self.url_bar.setText("")

        browser = BrowserView()
        browser.setUrl(qurl)
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_urlbar(qurl, browser))
        browser.loadFinished.connect(lambda _, i=i, browser=browser: self.tabs.setTabText(i, browser.page().title()))
        browser.page().featurePermissionRequested.connect(lambda feature, frame=browser.page(): self.feature_permission_requested(frame, feature))
        browser.page().iconChanged.connect(lambda icon: self.tabs.setTabIcon(i, icon))
        self.url_bar.setText("")

    def tab_open_doubleclick(self, i):
        if i == -1:
            self.add_new_tab()

    def current_tab_changed(self, i):
        qurl = self.tabs.currentWidget().url()
        self.update_urlbar(qurl, self.tabs.currentWidget())
        self.update_title(self.tabs.currentWidget())

    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            return sys.exit(0)
        self.tabs.removeTab(i)

    def current_browser(self):
        return self.tabs.currentWidget()

    def update_title(self, browser):
        qurl = self.url_bar.text()
        if browser != self.current_browser():
            return
        title = browser.page().title()
        self.setWindowTitle(f"{title} - Webby Explorer")

    def navigate_home(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        folder_name = "home"
        local_file_url = QUrl.fromLocalFile(os.path.join(script_dir, folder_name, "home.html"))
        self.current_browser().setUrl(QUrl(local_file_url))
        self.url_bar.setText("")

    def navigate_to_url(self):
        url = self.url_bar.text()
        if " " in url:
            self.current_browser().setUrl(QUrl("https://www.google.com/search?q="+url))
        elif url.startswith("https://") or url.startswith("http://"):
            self.current_browser().setUrl(QUrl(url))
        else:
            self.current_browser().setUrl(QUrl("http://"+url))

    def update_url(self, q):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        folder_name = "home"
        local_file_url = QUrl.fromLocalFile(os.path.join(script_dir, folder_name, "home.html"))

        if q == local_file_url:
                self.url_bar.setText("")
        else:
            self.url_bar.setText(q.toString())

    def update_urlbar(self, q, browser=None):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        folder_name = "home"
        local_file_url = QUrl.fromLocalFile(os.path.join(script_dir, folder_name, "home.html"))

        if browser != self.current_browser():
            return
        
        if q == local_file_url:
                self.url_bar.setText("")
        else:
            self.url_bar.setText(q.toString())
        self.url_bar.setCursorPosition(0)

    def feature_permission_requested(self, frame, feature):
        if feature == QWebEnginePage.OpenExternalLinks:
            reply = QMessageBox.question(self, 'Open Application Request', 'Do you want to open the application?', QMessageBox.Yes | QMessageBox.No)
            frame.setFeaturePermission(feature, reply == QMessageBox.Yes)
            frame.show()
            return QWebEnginePage.PermissionGrantedByUser if reply == QMessageBox.Yes else QWebEnginePage.PermissionDeniedByUser
        elif feature == QWebEnginePage.FileDialogPermission:
            return QWebEnginePage.PermissionGrantedByUser
    
    def create_line_edit(self):
        line_edit = LineEdit()
        line_edit.returnPressed.connect(self.navigate_to_url)
        self.navbar.addWidget(line_edit)
        self.tabs.currentChanged.connect(lambda _: self.update_url(self.current_browser().url(), line_edit))
    
    def toggle_fullscreen(self):
        current_browser = self.current_browser()

        if current_browser.isFullScreen():
            current_browser.showNormal()
        else:
            current_browser.showFullScreen()

app = QApplication(sys.argv)
QApplication.setApplicationName("Webby Explorer")
window = MainWindow()
icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'icon.ico')
window.setWindowIcon(QIcon(icon_path))
app.exec_()
