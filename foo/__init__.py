def show_logo():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    logo_window = LogoWindow()
    logo_window.show()
    app.processEvents()  # Ensure the logo is displayed
    return app
