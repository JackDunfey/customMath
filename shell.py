from test import run;
try:
    while True:
        run("shell",input("math@shell>"));
except KeyboardInterrupt:
    sys.exit(0);
# from test import debug;
# while True:
#     debug("shell", input("math@shell>"));
