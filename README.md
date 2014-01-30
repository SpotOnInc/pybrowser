# PyBrowser
PyBrowser is a pure python implementation of the [WebDriver JSON Wire Protocol](https://code.google.com/p/selenium/wiki/JsonWireProtocol). It was built as a better, faster, smaller, smarter, and simpiler alternative to Selenium. PyBrowser was built with testing in mind, but has applications across the board. PyBrowser not only implements a large percentage of the WebDriver protocol, but also comes with a large set of it's own tools to help make smart and fast browser-based scripts.


Example:
```python
# Right now chrome is the only supported Driver, this could easily change
from browser import ChromeDriver

driver = ChromeDriver()
driver.start()

# Create a new session (browser)
session = driver.new_session()

# Goto a website
session.goto("http://yoloswagtest.com/")

# Find an element with an id
session.find_id("clickableobj").click()

# Wait for something animated with jquery to finish
session.wait_jq_animation(".my_fadein_div")

# Wait for my_class to be visible (or exist) and then click it
session.find(css=".my_class", wait=5).click()

```