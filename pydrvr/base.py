"""
Base classes that can be inherited from to produce new drivers. See chrome.py
"""
import base64

# A list of functions drivers must implement
base_driver_functions = [
    "start", "stop", "is_running", "is_working", "get_status", "new_session"
]

base_session_functions = [
    "exit", "goto", "get_url", "get_html", "get_title", "maximize",
    "get_windows", "find", "find_link", "find_id", "find_name", "find_tag",
    "find_css", "find_class", "find_link_text", "wait_js", "execute",
    "screenshot"
]

base_element_functions = [
    "click", "type", "get_text", "is_visible"
]

def must_implement(functions):
    """
    Returns an inheritable class which defines a list of strict functions
    `functions`, that must be implemented by subclasses.
    """
    class _T(object):
        @classmethod
        def verify_implementation(cls):
            """
            Attempts to validate the sub-class implementation of a base
            inheritable class.
            """
            for func in functions:
                if not hasattr(cls, func):
                    raise NotImplementedError("%s must implement function %s" %
                        (cls.__name__, func))

        def __getattr__(self, attr):
            if attr in functions:
                raise NotImplementedError("%s must implement function `%s`" %
                    (self.__class__.__name__, attr))
            raise Exception("%s has no function or attribute `%s`" %
                (self.__class__.__name__, attr))
    return _T

class BaseDriver(must_implement(base_driver_functions)):
    """
    The base driver class which represents a bare-minimum API for drivers
    to implement.
    """

class BaseSession(must_implement(base_session_functions)):
    """
    The base session class which represents a single, isolated browser
    session/window. Different drivers may have different understandings of
    what a session is.
    """

    def has_jq(self):
        """
        Returns true if the current page has jQuery available...
        """
        return self.execute("return typeof jQuery !== 'undefined'")

    def wait_jq_animation(self, sel, visible=True):
        """
        Waits for a jquery animation on a selector `sel` to finish
        """
        base = 'return !$("%s").is(":animated")' % sel
        if visible:
            add = ' && $("%s").is(":visible")' % sel
        else: add = ''
        return self.wait_js(base+add, f=lambda a: a.get("value") == True)

    def wait_for_ajax(self):
        """
        Waits for all /jquery/ AJAX requests to finish.
        """
        return self.wait_js("return $.active == 0", f=lambda a: a.get("value") == True)

    def screenshot_to(self, f="screenshot.png"):
        """
        Takes a file location `f` and saves a PNG screenshot to that location.
        """
        with open(f, "w") as fi:
            fi.write(base64.b64decode(self.screenshot()))

class BaseElement(must_implement(base_element_functions)):
    """
    An interactible element on the page.
    """

class BaseWaiter(object):
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
