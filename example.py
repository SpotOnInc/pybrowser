from pydrvr import new_driver

# First, we need to open a new driver. By default the "chromedriver"
#  is provided. You can read more about this, or download it at
#  http://chromedriver.storage.googleapis.com/index.html
driver = new_driver("chrome")

# Once the driver is open, we can start a new instance of it. This is
#  implemented on the driver level, and for ChromeDriver it simply spawns
#  a new /usr/bin/chromedriver subprocess.
driver.start()

# Lets make sure the driver is running, and it's working properly...
print "Driver is running: %s and is working: %s" % (driver.is_running(), driver.is_working())

# Once our driver is started and working, we can spawn a new session. Sessions
#  can be though of as one browser window, but are completely isolated from
#  eachother.
sess = driver.new_session()

# Cool... now lets have some fun! Let's head over to google
sess.goto("http://google.com/")
assert sess.get_title() == "Google"

# Google that!
print sess.find_id(id="gbqfq")[0].type("pydrvr").click()

# Does google have jQuery available to us?
print sess.has_jq()

# Hmm... Maybe we should grab a screenshot...
sess.screenshot_to("google.png")

# Ok enough fun. Now let's safely close the session and driver. NOTE:
#  if these functions are not run, you WILL have issues with processes
#  saying alive. Always make sure to wrap dangerous code in try/except/finally
#  and make sure driver.stop() is called (it will recursivly close all
#  sessions, but it's a good idea to close those anyway)
sess.exit()
driver.stop()
