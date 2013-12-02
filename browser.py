import requests, subprocess, json, time
from pyquery import PyQuery

class BDriver(object):
    """
    The base driver class which represents a bare-minimum API for drivers
    to implement.
    """
    def __getattr__(self, i):
        if i in ["start", "stop", "is_running", "is_working", "get_status"]:
            raise NotImplementedError("Drivers should implement function %s")
        raise Exception("Driver's have no function/element %s" % i)

class Element(object):
    """
    An interactible element on the page.
    """

class Session(object):
    """
    A single browser (window) session.
    """
    def has_text(self, s):
        return (s in self.html())

class Waiter(object):
    """
    An object that specifies rules for waiting on a condition
    """

class ResultSet(object):
    def __init__(self, res):
        self.res = res

    def get(self, i):
        return self.res.get(i)

    def __getattr__(self, i):
        return getattr(self.res[0], i)

    def __getitem__(self, i):
        return self.res[i]

    def __len__(self):
        return len(self.res)

class ChromeDriver(BDriver):
    """
    A Driver implementation for Google Chrome.
    """
    def __init__(self, driver_path="/usr/bin/chromedriver", port=9123):
        self.driver_path = driver_path
        self.process = None
        self.port = port
        self.url = "http://localhost:%s" % (str(port)+"/%s")

        # Tracks any active sessions for exiting
        self.sessions = []

    def r_get(self, url, data=None):
        """
        Makes a get request to the chrome browser instance.

        :returns: Dictionary of data recieved from the servers endpoint
        :rtype: dict
        """
        r = requests.get(self.url % url, data=json.dumps(data or {}))
        r.raise_for_status()
        return r.json()

    def r_post(self, url, data=None):
        """
        Makes a post request to the chrome browser instance.

        :returns: Dictionary of data recieved from the servers endpoint
        :rtype: dict
        """
        r = requests.post(self.url % url, data=json.dumps(data or {}))
        r.raise_for_status()
        return r.json()

    def get_status(self):
        return self.r_get("status").get("status", -1)

    def is_running(self):
        return (self.process and self.process.poll() is None)

    def is_working(self):
        return (self.get_status() != -1)

    def start(self):
        self.process = subprocess.Popen([self.driver_path, "--port=%s" % self.port], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for i in range(0, 5):
            # This was purposely placed where it is...
            time.sleep(.5)
            if self.process.stdout.readline().startswith("Starting ChromeDriver"):
                return
        raise Exception("Could not start ChromeDriver!")

    def stop(self, kill_sessions=True):
        if self.is_running():
            if kill_sessions:
                for s in self.sessions:
                    if s.is_active():
                        s.exit(parent=True)
            self.process.kill()
            self.process.wait()
            return
        raise Exception("Cannot stop non-running driver")

    def new_session(self):
        data = self.r_post("session", {"desiredCapabilities": {}, "requiredCapabilities": {}})
        sess = ChromeDriverSession(self, data)
        self.sessions.append(sess)
        return sess

class ChromeDriverWaiter(Waiter):
    def __init__(self, ttl, cond, default, f, args, kwargs):
        self.ttl = ttl
        self.default = default
        self.cond = cond
        self.f = f
        self.args = args
        self.kwargs = kwargs

    def wait(self):
        for i in range(0, (self.ttl+1)*2):
            value = self.f(*self.args, **self.kwargs)
            if not self.cond(value):
                time.sleep(.5)
                continue
            return value
        return self.default

class ChromeDriverSession(Session):
    def __init__(self, parent, data):
        self.parent = parent
        self.data = data
        self.url = self.parent.url % ("session/%s" % self.data.get("sessionId"))
        self.window = self.get_windows()[0]

    def r(self, f, *args, **kwargs):
        r = f(*args, **kwargs)
        r.raise_for_status()
        data = r.json()
        return data

    def r_get(self, url, data=None):
        return self.r(requests.get, self.url+url, data=json.dumps(data or {}))

    def r_post(self, url, data=None):
        return self.r(requests.post, self.url+url, data=json.dumps(data or {}))

    def r_delete(self, url, data=None):
        return self.r(requests.delete, self.url+url, data=json.dumps(data or {}))

    def get_status(self):
        return self.r_get("")

    def is_active(self):
        return self.get_status().get("status", -1)

    def exit(self, parent=False):
        r = self.r_delete("")

    def goto(self, url):
        self.r_post("/url", {"url": url})

    def get_url(self):
        return self.r_get("/url").get("value")

    def html(self):
        return self.r_get("/source").get("value")

    def title(self):
        return self.r_get("/title").get("value")

    def maximize(self):
        return self.r_post("/window/%s/maximize" % self.window)

    def get_windows(self):
        return self.r_get("/window_handles").get("value")

    def finder(self, format, value, wait=0):
        data = self.r_post("/elements", {
            "using": format,
            "value": value
        })

        result = []
        for item in data.get("value", []):
            result.append(ChromeDriverElement(self, item))

        if wait and not len(result):
            return ChromeDriverWaiter(wait, lambda a: len(a), [], self.finder, [format, value], {"wait": 0}).wait()
        return ResultSet(result)

    def find(self, id=None, name=None, tag=None, css=None, cls=None, link=None, link_text=None, **kwargs):
        if id:
            return self.find_id(id, **kwargs)
        if name:
            return self.find_name(name, **kwargs)
        if tag:
            return self.find_tag(tag, **kwargs)
        if css:
            return self.find_css(css, **kwargs)
        if cls:
            return self.find_class(cls, **kwargs)
        if link_text:
            return self.find_link_text(link_text, **kwargs)
        if link:
            return self.find_link(link, **kwargs)

    def find_link(self, link, **kwargs):
        return self.find_css("a[href*='%s']" % link)

    def find_id(self, id, **kwargs):
        return self.finder("id", id, **kwargs)

    def find_name(self, name, **kwargs):
        return self.finder("name", name, **kwargs)

    def find_tag(self, name, **kwargs):
        return self.finder("tag name", name, **kwargs)

    def find_css(self, css, **kwargs):
        return self.finder("css selector", css, **kwargs)

    def find_class(self, cls, **kwargs):
        return self.finder("class name", cls, **kwargs)

    def find_link_text(self, link, **kwargs):
        q = "link text"
        if not kwargs.get("exact"):
            q = "partial "+q
        return self.finder(q, link, **kwargs)

    def wait_js(self, script, f=lambda a: a.get("value"), wait_time=5):
        return ChromeDriverWaiter(wait_time, f, False, self.r_post, ["/execute"], {"data": {"script": script}}).wait()

    def wait_jq_animation(self, sel):
        return self.wait_js('''$("%s").is(":animated")''' % sel, f=lambda a: a.get("value") == "false")

class ChromeDriverFinder(object):
    def __init__(self, parent, data):
        self.parent = parent
        self.data = data
        self.url = "/element/%s" % self.data.get("ELEMENT")

class ChromeDriverElement(object):
    def __init__(self, parent, data):
        self.parent = parent
        self.data = data
        self.url = "/element/%s" % self.data.get("ELEMENT")

    def r_get(self, url, data=None):
        return self.parent.r_get(self.url+url, data)

    def r_post(self, url, data=None):
        return self.parent.r_post(self.url+url, data)

    def click(self):
        data = self.r_post("/click")
        if data.get("status") != 0:
            raise Exception("ChromeDriverElement.click error: %s" % data.get("value").get("message"))
        return self

    def type(self, value=""):
        self.r_post("/value", {'value': value.split()})
        return self

    def text(self):
        r = self.r_get("/text")
        return r.get("value")

    def visible(self, wait_for=None, wait_time=5):
        if wait_for is not None:
            return ChromeDriverWaiter(wait_time, lambda a: a.get("value") == wait_for, None, self.r_get, ["/displayed"], {}).wait()
        r = self.r_get("/displayed")
        return r.get("value")

DRIVERS = {
    "chrome": ChromeDriver
}

# Do you even function bro
def Driver(s="chrome"):
    """
    Function that returns a driver instance based on a name (string) of
    the driver. Throws exception if the driver is not recognized.
    """
    if not s in DRIVERS:
        raise Exception("No driver support for '%s'" % s)
    return DRIVERS[s]()

class KEYS(object):
    """
    Enum for keys that can be sent to the browser
    """
    NULL = u"\uE000"
    CANCEL = u"\uE001"
    HELP = u"\uE002"
    BACKSPACE = u"\uE003"
    TAB = u"\uE004"
    CLEAR = u"\uE005"
    RETURN = u"\uE006"
    ENTER = u"\uE007"
    SHIFT = u"\uE008"
    CONTROL = u"\uE009"
    ALT = u"\uE00A"
    PAUSE = u"\uE00B"
    ESCAPE = u"\uE00C"
    SPACE = u"\uE00D"
    PAGEUP = u"\uE00E"
    PAGEDOWN = u"\uE00F"
    END = u"\uE010"
    HOME = u"\uE011"
    LEFTARROW = u"\uE012"
    UPARROW = u"\uE013"
    RIGHTARROW = u"\uE014"
    DOWNARROW = u"\uE015"
    INSERT = u"\uE016"
    DELETE = u"\uE017"
    SEMICOLON = u"\uE018"
    EQUALS = u"\uE019"
    NUM0 = u"\uE01A"
    NUM1 = u"\uE01B"
    NUM2 = u"\uE01C"
    NUM3 = u"\uE01D"
    NUM4 = u"\uE01E"
    NUM5 = u"\uE01F"
    NUM6 = u"\uE020"
    NUM7 = u"\uE021"
    NUM8 = u"\uE022"
    NUM9 = u"\uE023"

if __name__ == "__main__":
    driver = ChromeDriver()
    driver.start()
    print driver.is_running()
    print driver.is_working()
    sess = driver.new_session()
    sess.goto("http://google.com/")
    print sess.find_id(id="gbqfq")[0].kb("test").click()
    assert sess.title() == "Google"
    sess.exit()
    driver.stop()