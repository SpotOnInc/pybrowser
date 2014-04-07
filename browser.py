import requests, subprocess, json, time

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
    """
    A set of element results returned from a selector query. This allows
    some batch operations, such as .has and .get
    """
    def __init__(self, res):
        self.res = res

    def get(self, i):
        """
        Returns result at index `i`
        """
        return self.res.get(i)

    def has(self, amount=None):
        """
        Returns whether the ResultSet has any results in it, or if `amount`
        is specified, whether the number of results matches `amount`
        """
        if amount is not None:
            return len(self.res) == amount
        return len(self.res)

    def __getattr__(self, i):
        return getattr(self.res[0], i)

    def __getitem__(self, i):
        return self.res[i]

    def __len__(self):
        return len(self.res)

class ChromeDriver(BDriver):
    """
    A Driver implementation for Google Chrome. This uses the downloaded
    chromedriver (see http://chromedriver.storage.googleapis.com/index.html)
    which should (by default) be located at /usr/bin/chromedriver. This
    is configurable using the `driver_path` option. Additionally, one
    can specify a port for ChromeDriver to run on, although it defaults
    to 9123. Note, you should make this different if more then one instance
    of this class needs to run at once.
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
        """
        Returns the status of this driver.
        """
        return self.r_get("status").get("status", -1)

    def is_running(self):
        """
        Returns whether the chromedriver process is still running.
        """
        return (self.process and self.process.poll() is None)

    def is_working(self):
        """
        Returns whether the driver is actually working (e.g. useable).
        """
        return (self.get_status() != -1)

    def start(self):
        """
        Starts a subprocess of the webdriver binary, passing in our port
        argument. This will try 5 times to start a webdriver, and tests
        each time whether the instance is running based on ouput text.

        Will raise an exception if it cannot start the process.
        """
        self.process = subprocess.Popen([self.driver_path, "--port=%s" % self.port],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for i in range(0, 5):
            # This was purposely placed where it is...
            time.sleep(.5)
            if self.process.stdout.readline().startswith("Starting ChromeDriver"):
                if not self.is_running:
                    raise Exception("Could not start ChromeDriver: %s" %
                        self.process.stdout.readlines())
                return
        raise Exception("Could not start ChromeDriver!")

    def stop(self, kill_sessions=True):
        """
        Stops the webdriver subprocess if it exists. This should /really/
        always be run before quitting.
        """
        if self.is_running():
            if kill_sessions:
                for s in self.sessions:
                    if s.is_active():
                        s.exit()
            self.process.kill()
            self.process.wait()
            return
        raise Exception("Cannot stop non-running driver")

    def new_session(self):
        """
        Creates and returns a new ChromeDriverSession. One driver can have
        multiple sessions, and thus this can be called many times in
        succession
        """
        data = self.r_post("session", {"desiredCapabilities": {}, "requiredCapabilities": {}})
        sess = ChromeDriverSession(self, data)
        self.sessions.append(sess)
        return sess

class ChromeDriverWaiter(Waiter):
    """
    A utility class that helps with waiting for conditions to be met

    TODO: rewrite me, make this whole thing readable
    """
    def __init__(self, ttl, cond, default, f, args, kwargs, wrap=lambda a: a):
        self.ttl = ttl
        self.default = default
        self.cond = cond
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.wrap = wrap

    def wait(self):
        for i in range(0, (self.ttl+1)*2):
            value = self.f(*self.args, **self.kwargs)
            if not self.cond(value):
                time.sleep(.5)
                continue
            return self.wrap(value)
        return self.wrap(self.default)

class ChromeDriverSession(Session):
    """
    A single browser session inside the chrome driver. Represents one
    browser instance.
    """
    def __init__(self, parent, data):
        self.parent = parent
        self.data = data
        self.url = self.parent.url % ("session/%s" % self.data.get("sessionId"))
        self.window = self.get_windows()[0]

    def r(self, f, *args, **kwargs):
        """
        Basic request wrapper that will raise exception on non 200 return
        codes
        """
        r = f(*args, **kwargs)
        r.raise_for_status()
        data = r.json()
        return data

    def r_get(self, url, data=None):
        """
        Fire a get request on this session
        """
        return self.r(requests.get, self.url+url, data=json.dumps(data or {}))

    def r_post(self, url, data=None):
        """
        Fire a post request on this session
        """
        return self.r(requests.post, self.url+url, data=json.dumps(data or {}))

    def r_delete(self, url, data=None):
        """
        Fire a delete request on this session
        """
        return self.r(requests.delete, self.url+url, data=json.dumps(data or {}))

    def is_active(self):
        """
        TODO
        """
        return True

    def exit(self):
        """
        Closes this browser session
        """
        self.r_delete("")

    def goto(self, url):
        """
        Send the browser to the url `url`.
        """
        self.r_post("/url", {"url": url})

    def get_url(self):
        """
        Returns the current url the browser session is at.
        """
        return self.r_get("/url").get("value")

    def html(self):
        """
        Returns the html source of the current loaded webpage
        """
        return self.r_get("/source").get("value")

    def title(self):
        """
        Returns the title of the current loaded webpage
        """
        return self.r_get("/title").get("value")

    def maximize(self):
        """
        Maxamizes the browser window
        """
        return self.r_post("/window/%s/maximize" % self.window)

    def get_windows(self):
        """
        Returns the windows for this session
        """
        return self.r_get("/window_handles").get("value")

    def finder(self, format, value, wait=0, **kwargs):
        data = self.r_post("/elements", {
            "using": format,
            "value": value
        })

        result = []
        for item in data.get("value", []):
            result.append(ChromeDriverElement(self, item))

        if wait and not len(result):
            return ChromeDriverWaiter(wait, lambda a: len(a), [], self.finder, [format, value],
                {"wait": 0}, ResultSet).wait()
        return ResultSet(result)

    def find(self, **kwargs):
        if kwargs.get("id"):
            return self.find_id(kwargs.get("id"), **kwargs)
        if kwargs.get("name"):
            return self.find_name(kwargs.get("name"), **kwargs)
        if kwargs.get("tag"):
            return self.find_tag(kwargs.get("tag"), **kwargs)
        if kwargs.get("css"):
            return self.find_css(kwargs.get("css"), **kwargs)
        if kwargs.get("cls"):
            return self.find_class(kwargs.get("cls"), **kwargs)
        if kwargs.get("link_text"):
            return self.find_link_text(kwargs.get("link_text"), **kwargs)
        if kwargs.get("link"):
            return self.find_link(kwargs.get("link"), **kwargs)

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
        return ChromeDriverWaiter(wait_time, f, False, self.r_post, ["/execute"],
            {"data": {"script": script, "args": []}}).wait()

    def wait_jq_animation(self, sel, visible=True):
        base = 'return !$("%s").is(":animated")' % sel
        if visible:
            add = ' && $("%s").is(":visible")' % sel
        else: add = ''
        return self.wait_js(base+add, f=lambda a: a.get("value") == True)

    def wait_for_ajax(self):
        return self.wait_js("return $.active == 0", f=lambda a: a.get("value") == True)

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
            raise Exception("ChromeDriverElement.click error: %s" %
                data.get("value").get("message"))
        return self

    def type(self, value="", safe=False):
        """
        If safe is true, go one by one with short sleep
        """
        if safe:
            for value in value.split():
                self.type(value, safe=False)
                time.sleep(.5)
        else:
            self.r_post("/value", {'value': value.split()})
        return self

    def text(self):
        r = self.r_get("/text")
        return r.get("value")

    def visible(self, wait_for=None, wait_time=5):
        if wait_for is not None:
            return ChromeDriverWaiter(wait_time, lambda a: a.get("value") == wait_for, None,
                self.r_get, ["/displayed"], {}).wait()
        r = self.r_get("/displayed")
        return r.get("value")

DRIVERS = {
    "chrome": ChromeDriver
}

# Do you even function bro
def new_driver(name="chrome"):
    """
    Function that returns a driver instance based on a name (string) of
    the driver. Throws exception if the driver is not recognized.
    """
    if not name in DRIVERS:
        raise Exception("No driver support for '%s'" % name)
    return DRIVERS[name]()

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
    driver = new_driver("chrome")
    driver.start()
    print driver.is_running()
    print driver.is_working()
    sess = driver.new_session()
    sess.goto("http://google.com/")
    print sess.find_id(id="gbqfq")[0].kb("test").click()
    assert sess.title() == "Google"
    sess.exit()
    driver.stop()
