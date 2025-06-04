
def is_raspberry_pi():
    try:
        with open("/proc/cpuinfo", "r") as f:
            if "Raspberry Pi" in f.read():
                return True
    except:
        pass
    import platform
    return platform.machine().startswith("arm") and \
        "raspberrypi" in platform.uname().nodename