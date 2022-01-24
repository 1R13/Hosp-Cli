import mariadb  # mariadb must be installed via 'pip3 install mariadb' or 'python3 -m pip install mariadb'
import datetime  # as well as python-dateutil on some systems

from Personal import Personal
from patient import Patient
from dateutil import relativedelta
from getpass import getpass

# methode for connecting with the iue database
def connect(pw):
    conn = mariadb.connect(
        user="USERNAME",
        password=pw,
        host="HOSTIP/DOMAIN",
        port="PORT",
        database="SCHEMA"
    )
    return conn

# the menu points not covered by 'PatientMethods'


class MenuPoints:
    def showMenu(options):
        print("")
        for opt in options:
            print(" [%s]" % opt)
        print("")

    def showTables(c):
        print("\n")
        c.execute("show tables;")
        for cur in c:
            print("[%s]" % cur[0])
        print("")

    def selectTable(c, tableName):
        c.execute("SELECT * FROM %s" % tableName)
        for cur in c:
            print(cur)

    def commit(s):
        print("commiting…")
        s.commit()

    # def showPatients(c):

# the menu options for patient management
class PatientMethods:
    def importPatients(c):
        patients = []
        for cur in c:
            patients.append(Patient(cur[0], cur[1], cur[2], cur[3]))

        return patients

    def displayPatients(list):      # displaying given Patient objects in a list
        print("")
        for p in list:
            print(20 * "#")
            print("Patient ID : %i" % p.ID)
            print("Name : %s, %s" % (p.last_name, p.first_name))
            print("Age :", relativedelta.relativedelta(datetime.date.today(), p.birthdate).years)
            print("Birthday :", p.birthdate)
            print("")
        print("")

    def searchPatient(c):
        term = input("Enter term : ")
        raw_patients = []
        c.execute("SELECT * FROM Patient;")
        for p in c:
            for value in p:
                if value == term:
                    raw_patients.append(p)
                    break

        PatientMethods.displayPatients(PatientMethods.importPatients(raw_patients))

    def takeInPatient(c):   # this methode uses the takeInPatient() stored procedure from the server
        print("creating new patient…")
        first_name = input("Enter first name : ")   # prompting the user within the method for arguments, so function
        last_name = input("Enter last name : ")     # can be called without arguments from the menu
        birthdate = input("Enter birthdate (YYYY-MM-DD) : ")
        c.execute("SELECT * FROM Patient WHERE vorname = \"%s\" AND nachname = \"%s\" AND geburtsdatum = \"%s\";" % (first_name, last_name, birthdate))
        result = []
        for cur in c:
            result.append(cur)
        if len(result) > 0:
            print("patient with attribute combination is already present, aborting!")
            return 1
        else:
            c.execute("CALL takeInPatient(\"%s\", \"%s\", \"%s\");" % (first_name, last_name, birthdate))
        for cur in c:
            print(cur)


class StaffMethods:

    def showRoles(roles):
        for r in roles:
            print(" %i, %s" % (r, roles[r]))
        return 0

    def importRoles(c):
        roles = {}
        index = 1
        c.execute("SELECT * FROM Rolle;")
        for cur in c:
            roles[index] = cur[1]
            index += 1
        # print(roles)
        return roles

    def displayStaff(list, roles):
        print("")
        for s in list:
            print(20*"#")
            print("Personal ID : %i" % s.ID)
            print("Name : '%s', '%s'" % (s.first_name, s.last_name))
            print("Role : %s[%i]" % (roles[s.role], s.role))
            print("")
        print("")

    def importStaff(list):      # converts raw staff tuples into Personal objects
        staff = []
        for s in list:
            staff.append(Personal(s[0], s[1], s[2], s[3]))
        return staff

    def searchStaff(c, term, roles):
        raw_staff = []
        for r in roles:
            if roles[r] == term:
                c.execute("SELECT * FROM Personal WHERE idRolle = %i" %r)
                for cur in c:
                    raw_staff.append(cur)
                StaffMethods.displayStaff(StaffMethods.importStaff(raw_staff), roles)
                return 0

        c.execute("SELECT * FROM Personal;")
        for cur in c:
            for value in cur:
                if value == term:
                    raw_staff.append(cur)
        StaffMethods.displayStaff(StaffMethods.importStaff(raw_staff), roles)
        return 0

    def addStaff(c, roles):
        print("creating new staff entry…")
        first_name = input("Enter new first name : ")
        last_name = input("Enter new last_name : ")

        role = ""

        while not type(role) == int:
            try:
                role = int(input("Enter new role ID : "))
            except Exception as err:
                print(err)
        station = ""
        while not type(station) == int:
            try:
                station = int(input("Enter new station ID : "))
            except Exception as err:
                print(err)
        c.execute("SELECT * FROM Personal WHERE vorname = \"%s\" and nachname = \"%s\" and idRolle = \"%i\";")
        results = []
        for cur in c:
            results.append(cur)
        if len(results) > 0:
            print("Found existing Staff")
            StaffMethods.displayStaff(StaffMethods.importStaff(results), roles)
            return 1
        else:
            c.execute("CALL addPersonal(\"%s\", \"%s\", %i, %i);" % (first_name, last_name, role, station))



def main():
    exit = False
    options = {"showMenu": MenuPoints.showMenu,
               "showTables": MenuPoints.showTables,
               "selectTable": MenuPoints.selectTable,
               "displayPatients": PatientMethods.displayPatients,
               "searchPatient": PatientMethods.searchPatient,
               "takeInPatient": PatientMethods.takeInPatient,
               "displayStaff": StaffMethods.displayStaff,
               "searchStaff" : StaffMethods.searchStaff,
               "addStaff": StaffMethods.addStaff,
               "showRoles": StaffMethods.showRoles}
    try:
        session = connect(getpass("Enter password for user 'dbn15' : "))

    except Exception as err:
        print(err)
        quit()

    MenuPoints.showMenu(options)
    roles = StaffMethods.importRoles(session.cursor())
    while not exit:
        try:
            _input = input("(menuOption|x) : ")     # asks for a menu point or x for quitting
            if not _input == "x":
                if _input == "showMenu" or _input == "help":
                    options["showMenu"](options)
                elif _input == "selectTable":
                    options[_input](session.cursor(), input("Enter table name : "))
                elif _input == "displayPatients":
                    c = session.cursor()
                    c.execute("SELECT * FROM Patient;")     # prepares the cursor results to be displayed by PatientMethods.displayPatients()
                    raw_patients = []
                    for cur in c:
                        raw_patients.append(cur)
                    options[_input](PatientMethods.importPatients(raw_patients))
                elif _input == "console":
                    while not exit:
                        statement = input("(statement?) : ")
                        if not statement == "x":
                            c = session.cursor()
                            c.execute(statement)
                            for cur in c:
                                print(cur)
                elif _input == "commit":
                    MenuPoints.commit(session)
                elif _input == "displayStaff":
                    c = session.cursor()

                    c.execute("SELECT * FROM Personal;")
                    raw_staff = []
                    for cur in c:
                        raw_staff.append(cur)
                    options[_input](StaffMethods.importStaff(raw_staff), roles)
                elif _input == "searchStaff":
                    term = input("Enter search term : ")
                    StaffMethods.searchStaff(session.cursor(), term, roles)
                elif _input == "addStaff":
                    options[_input](session.cursor(), roles)
                elif _input == "showRoles":
                    options[_input](roles)
                else:
                    options[_input](session.cursor())

            else:
                exit = True
        except Exception as err:
            print(err)
    print("Committing Changes…")
    session.commit()


main()
