"""
Base classes that can be inherited from to produce new drivers. See chrome.py
"""

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
