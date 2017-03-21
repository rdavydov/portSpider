import MySQLdb
import socket
import datetime
import sys
import ipaddress
import threading
import os

BLUE, RED, WHITE, YELLOW, MAGENTA, GREEN, END = '\33[1;94m', '\033[1;91m', '\33[1;97m', '\33[1;93m', '\033[1;35m', '\033[1;32m', '\033[0m'

def checkSQL(host, port):
    try:
        con = MySQLdb.connect(host=host, user='root', passwd='', connect_timeout=sqlTimeout)
    except:
        return ["login-error"]

    try:
        cursor = con.cursor()
        cursor.execute("SHOW DATABASES")
        dbs = cursor.fetchall()
    except:
        dbs = ["-"]

    try:
        cursor = con.cursor()
        cursor.execute("SELECT VERSION()")
        serverVersion = str(cursor.fetchone())
    except:
        serverVersion = "-"

    return ["success", serverVersion, dbs]

def coreOptions():
    options = [["network", "IP range to scan", ""], ["port", "Port to scan.", "3306"],
               ["port-timeout", "Timeout (in sec) for port 80.", "0.3"], ["sql-timeout", "Timeout (in sec) for the database connection.", "3"],
               ["threads", "Number of threads to run.", "50"],
               ["checkauth", "Connect to the server and perform tests.", "true"], ["verbose", "Show verbose output.", "true"]]
    return options


def createIPList(network):
    net4 = ipaddress.ip_network(network)
    ipList = []
    for x in net4.hosts():
        ipList.append(x)
    return ipList

def print1(data):
    if verbose:
        print(data)

def checkServer(address, port):
    s = socket.socket()
    s.settimeout(float(portTimeout))
    try:
        s.connect((address, port))
        s.close()
        return True
    except socket.error:
        s.close()
        return False
    except:
        s.close()
        return "FAIL"


def writeToFile(line):
    file = open(fileName, "a")
    file.write(line)
    file.close()


def restart_line():
    sys.stdout.write('\r')
    sys.stdout.flush()


def statusWidget():
    sys.stdout.write(GREEN + "[" + status + "] " + YELLOW + str(ipID) + GREEN + " / " + YELLOW + str(
        allIPs) + GREEN + " hosts done." + END)
    restart_line()
    sys.stdout.flush()


def scan(i):
    global ipID
    global status
    global openPorts
    global done
    for ip in ips[i]:
        if stop:
            sys.exit()

        if (str(ip) == "0"):
            continue
        ipID = ipID + 1
        status = (ipID / allIPs) * 100
        status = format(round(status, 2))
        status = str(status) + "%"
        stringIP = str(ip)
        isUp = checkServer(stringIP, port)

        if isUp != "FAIL":
            if isUp:
                openPorts = openPorts + 1
                print1(GREEN + "[+] Port " + str(port) + " is open on '" + stringIP + "'" + END)

                if checkauth:
                    mysqlStatusReason = "UNKNOWN ERROR"
                    mysql = checkSQL(stringIP, port)
                    if mysql[0] == "login-error":
                        mysqlStatus = False
                        mysqlStatusReason = "CONNECTION ERROR"
                        print1(RED + "[!] Failed connecting to the database on '" + stringIP + "'. ERROR: " + mysqlStatusReason + END)
                    elif mysql[0] == "permission-error":
                        mysqlStatus = False
                        mysqlStatusReason = "PERMISSION ERROR"
                        print1(RED + "[!] Failed connecting to the database on '" + stringIP + "'. ERROR: " + mysqlStatusReason + END)
                    elif mysql[0] == "success":
                        mysqlStatus = True
                        version = mysql[1]
                        dbs = mysql[2]

                        dbsList = ""
                        for db in dbs:
                            dbsList = dbsList + str(db) + ", "
                        if dbsList != "":
                            dbsList = dbsList[:-2]
                        else:
                            dbsList = "-"

                        print1(GREEN + "[+] Open database found:\n\tIP: " + stringIP + "\n\t" + "MySQL version: " + str(version) + "\n\tDB's: " + dbsList + "\n")

                    else:
                        print1(RED + "[!] Failed connecting to the database on '" + stringIP + "'. ERROR: " + mysqlStatusReason + END)
                        mysqlStatus = False

                    if mysqlStatus:
                        logLine = stringIP + " - " + str(port) + " OPEN" + " - " + "OPEN DATABASE - Version: " + version + " - " + " DB's: " + dbsList + "\n"
                    else:
                        logLine = stringIP + " - " + str(port) + " OPEN" + " - DB SCAN ERROR: " + mysqlStatusReason + "\n"
                    logLines.append(logLine)
                else:
                    logLine = stringIP + " - " + str(port) + " OPEN\n"
                    logLines.append(logLine)
            elif not isUp:
                print1(RED + "[-] Port " + str(port) + " is closed on '" + stringIP + "'" + END)
        else:
            print1(RED + "[!] Failed connecting to '" + stringIP + "'" + END)
    done = done + 1


def core(moduleOptions):
    print(
        "\n" + GREEN + "MYSQL module by @xdavidhu. Scanning subnet '" + YELLOW + moduleOptions[0][2] + GREEN + "'...\n")

    global status
    global ipID
    global fileName
    global allIPs
    global portTimeout
    global titleTimeout
    global ips
    global threadCount
    global done
    global verbose
    global stop
    global port
    global ipID
    global openPorts
    global logLines
    global checkauth
    global sqlTimeout
    logLines = []
    stop = False
    done = 0

    try:
        port = int(moduleOptions[1][2])
    except:
        print(RED + "[!] Invalid port. Exiting...\n")
        return
    portTimeout = moduleOptions[2][2]
    network = moduleOptions[0][2]
    sqlTimeout = moduleOptions[3][2]
    threadCount = int(moduleOptions[4][2])
    checkauth = moduleOptions[5][2]
    verbose = moduleOptions[6][2]

    try:
        sqlTimeout = int(sqlTimeout)
    except:
        print(RED + "[!] Invalid sql-timeout. Exiting...\n")
        return

    if verbose == "true":
        verbose = True
    else:
        verbose = False

    if checkauth == "true":
        checkauth = True
    else:
        checkauth = False

    try:
        ipList = createIPList(network)
    except:
        print(RED + "[!] Invalid subnet. Exiting...\n")
        return
    allIPs = len(ipList)

    h = threadCount
    w = int(allIPs / threadCount)
    if (w < allIPs / threadCount):
        w = w + 1
    ips = [[0 for x in range(w)] for y in range(h)]
    i = 0
    i2 = [0 for x in range(h)]


    for ip in ipList:
        if (i + 1 > threadCount):
            i = 0
        ips[i][i2[i]] = ip
        i2[i] = i2[i] + 1;
        i = i + 1
    i = datetime.datetime.now()
    i = str(i).replace(" ", "_")
    i = str(i).replace(":", "-")
    if not os.path.exists("logs"):
        os.makedirs("logs")
    fileName = "logs/log-mysql-portSpider-" + i + ".log"

    file = open(fileName, 'w')
    file.write("subnet: " + network + "\n")
    file.close()

    ipID = 0
    openPorts = 0
    threads = []
    for i in range(threadCount):
        i -= 1
        t = threading.Thread(target=scan, args=(i,))
        t.daemon = True
        threads.append(t)
        t.start()

    try:
        while done != threadCount:
                pass
                statusWidget()
    except KeyboardInterrupt:
            stop = True
            verbose = False
            print("\n" + RED + "[I] Stopping..." + END)

    for logLine in logLines:
        try:
            writeToFile(logLine)
        except:
            writeToFile("WRITING-ERROR")

    print("\n\n" + GREEN + "[I] MYSQL module done. Results saved to '" + YELLOW + fileName + GREEN + "'.\n")
