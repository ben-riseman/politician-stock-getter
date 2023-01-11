import selenium, time, pandas
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.relative_locator import locate_with
from webdriver_manager.chrome import ChromeDriverManager



SAVE_TO_CSV = True
DO_WEBSCRAPE = True

pandas.set_option('display.max_rows', 500)
pandas.set_option('display.max_columns', 20)
pandas.set_option('display.width', 1000)

url = "https://efdsearch.senate.gov/search/home/"

list_of_names = ["Manchin", "Tuberville"]

list_of_profiles = []

class Profile():
    def __init__(self, name, ptr_list):
        self.name = name
        self.ptr_list = ptr_list
        self.current_holdings = pandas.DataFrame(data = None)

    def add_df(self, date, df):
        found = False
        for d in self.ptr_list:
            if list(d.keys())[0] == date:
                found = True
                print("Scrubbing duplicate of", date)
                break

        self.ptr_list.append({date : df}) if found == False else None

    def print_all(self):
        print("Name:", self.name)
        for ptr in self.ptr_list:
            for date in ptr:
                print("Date:", date)
                print(ptr[date])

    def save_to_csv(self, index = 0):
        requested_df = self.ptr_list[index]
        string = self.name + "_" + requested_df[0] + "_PTR.csv"
        print("Saving as", string)
        requested_df[1].to_csv(string, index = False)


def record_to_master(dfList):
    file = open("ptr_master.txt", "r")
    lines = file.readlines()

    for df in dfList:
        name = df[0]
        date = df[1]
        fileName = df[2]

        lines.append(name + " " + date + " " + fileName + "\n")

        file.close()
    
    file = open("ptr_master.txt", "w")
    [file.write(line) for line in lines]
    file.close()


def read_master():
    file = open("ptr_master.txt", "r")
    lines = file.readlines()
    file.close()
    return lines

def construct_profile(line):
    l = line.split(" ", 2)
    name = l[0]
    date = l[1]
    fileName = l[2]

    try:
        df = pandas.read_csv(fileName)
    except Exception:
        print("File somehow not found... returning")
        return

    foundProfile = False

    for profile in list_of_profiles:
        if profile.name == name:
            foundProfile = True
            profile.add_df(date, df)
            break

    if foundProfile == False:
        list_of_profiles.append(Profile(name, [{date : df}]))
        
    
def checked_find(byStr, valueStr, tryCount = 10):
    x = None
    
    for i in range(tryCount):
        try:
            x = driver.find_element(by=byStr, value=valueStr)
            break
        except NoSuchElementException as e:
            print('Retry in 1 second')
            time.sleep(1)
    else:
        print("Element not found!", valueStr)

    if x != None:
        return x

def close_last_tab():
    if (len(driver.window_handles) == 2):
        driver.switch_to.window(window_name=driver.window_handles[0])
        driver.close()
        driver.switch_to.window(window_name=driver.window_handles[0])

def dictify(header_list, big_list):
    x = {k : [] for k in header_list}
    for row in big_list:
        count = 0
        for k in x.keys():
            x[k].append(row[count])
            count += 1
    return x

def print_profiles():
    [x.print_all() for x in list_of_profiles]

def create_min_max(df : pandas.DataFrame) -> pandas.DataFrame:

    df2 = df.copy()

    try:
        #print(df2["Amount"].str.replace(r'\D', ''))
        l = df2["Amount"].str.split(expand = True)
        mini = l[0].str.replace(r'\D', '')
        maxi = l[2].str.replace(r'\D', '')
        print(mini, maxi)
    except Exception as ex:
        print(ex)

    try:
        #print(df2["Amount"].str.replace(r'\D', ''))
        l = df2["Value"].str.split(expand = True)
        mini = l[0].str.replace(r'\D', '')
        maxi = l[2].str.replace(r'\D', '')
        print(mini, maxi)
    except Exception as ex:
        print(ex)

    df2.insert(7, "Minimum Value", pandas.to_numeric(mini))
    df2.insert(8, "Maximum Value", pandas.to_numeric(maxi))

    return df2


def create_median(df : pandas.DataFrame) -> pandas.DataFrame:
    """ Generates a median column in the provided DataFrame. Returns a modified copy. """

    df2 = df.copy()

    print(df2)

    

    try:

        df2["Minimum Value"] = df2["Minimum Value"].str.replace(r'\D', '')
        df2["Maximum Value"] = df2["Maximum Value"].str.replace(r'\D', '')

    except Exception as ex:
        print(ex)

    else:

        df2["Minimum Value"] = df2["Minimum Value"]
        df2["Maximum Value"] = df2["Maximum Value"]

    df2.insert(9, "median_value", (pandas.to_numeric(df2["Minimum Value"]) +
                           pandas.to_numeric(df2["Maximum Value"])) / 2)

    return df2

def add_amounts(df: pandas.DataFrame) -> pandas.DataFrame:

    df2 = df.copy()
    df2 = create_min_max(df2)
    df2 = create_median(df2)
    return df2

def webScrape(list_of_names):
    driver.get(url)

    ptr_master_lines = read_master()
    
    firstCheckbox = checked_find("id", "agree_statement").click()

    get_annual(list_of_names)

    #driver.get(url)
    
    for last_name in list_of_names:

        driver.get(url)
        
        print("Name:", last_name)

        lastNameBox = checked_find("id", "lastName").send_keys(last_name)
        transactionCheckbox = checked_find("xpath", "/html/body/div[1]/main/div/div/div[5]/div/form/fieldset[3]/div/div/div/div[1]/div[2]/label/input").click()
        #annualCheckbox = checked_find("xpath", "/html/body/div[1]/main/div/div/div[5]/div/form/fieldset[3]/div/div/div/div[1]/div[1]/label/input").click()

        search_button = checked_find("xpath", "//button[text()='Search Reports']").click()

        date_sort = checked_find("xpath", "//th[text()='Date Received/Filed']")
        date_sort.click()
        date_sort.click()

        time.sleep(1)

        reports = checked_find("xpath", "/html/body/div[1]/main/div/div/div[6]/div/div/div/table/tbody/tr[1]/td[4]/a")
        date_of_report = checked_find("xpath", "/html/body/div[1]/main/div/div/div[6]/div/div/div/table/tbody/tr[1]/td[5]")

        if reports == None or date_of_report == None:
            continue
        
        #date_of_report.text = date_of_report.text.replace("/", "-")
        date_text = date_of_report.text.replace("/", "-")
        
        string = last_name + "_" + date_text + "_PTR.csv"
        recordString = last_name + " " + date_text + " " + string

        if recordString + "\n" in ptr_master_lines:
            print("Found PTR already for", last_name, date_of_report)
            print("Constructing (or adding) to profile...")
            construct_profile(recordString)
            continue
                    
        reports.click()

        time.sleep(1)
        
        close_last_tab()

        transaction_headers = checked_find("xpath", "/html/body/div/main/div/div/section/div/div/table/thead")
        transaction_table = checked_find("xpath", "/html/body/div/main/div/div/section/div/div/table/tbody")

        if transaction_headers == None or transaction_table == None:
            continue

        rows = transaction_table.find_elements(by="tag name", value="tr")
        headers = transaction_headers.find_elements(by="tag name", value="tr")
        
        big_list = []
        header_list = []

        for header in headers:
            cols = header.find_elements(by="tag name", value = "th")
            for col in cols:
                header_list.append(col.text)

        for row in rows:
            lil_list = []
            cols = row.find_elements(by="tag name", value = "td")
            for col in cols:
                t = col.text
                if "/" in col.text:
                    t = col.text.replace("/", "-")
                lil_list.append(t)
            big_list.append(lil_list)


        trans_dict = dictify(header_list, big_list)

        df = pandas.DataFrame.from_dict(trans_dict)

        list_of_profiles.append(Profile(last_name, [{date_text: df}]))

        
        print("Date of Report:", date_text)
        print(df)
        print("Done with", last_name)

        df = add_amounts(df)

        if SAVE_TO_CSV:
            print(string)
            df.to_csv(string, index = False)
            record_to_master([[last_name, date_text, string]])

    driver.quit()

def get_annual(list_of_names):
    
    for last_name in list_of_names:

        driver.get(url)
        
        print("Name:", last_name)

        lastNameBox = checked_find("id", "lastName").send_keys(last_name)
        #transactionCheckbox = checked_find("xpath", "/html/body/div[1]/main/div/div/div[5]/div/form/fieldset[3]/div/div/div/div[1]/div[2]/label/input").click()
        annualCheckbox = checked_find("xpath", "/html/body/div[1]/main/div/div/div[5]/div/form/fieldset[3]/div/div/div/div[1]/div[1]/label/input").click()

        search_button = checked_find("xpath", "//button[text()='Search Reports']").click()

        date_sort = checked_find("xpath", "//th[text()='Date Received/Filed']")
        date_sort.click()
        date_sort.click()

        time.sleep(1)

        reports = checked_find("xpath", "/html/body/div[1]/main/div/div/div[6]/div/div/div/table/tbody/tr[1]/td[4]/a")
        date_of_report = checked_find("xpath", "/html/body/div[1]/main/div/div/div[6]/div/div/div/table/tbody/tr[1]/td[5]")

        if reports == None or date_of_report == None:
            continue
        
        #date_of_report.text = date_of_report.text.replace("/", "-")
        date_text = date_of_report.text.replace("/", "-")
        
        string = last_name + "_" + date_text + "_ANNUAL.csv"
        recordString = last_name + " " + date_text + " " + string

        if recordString + "\n" in ptr_master_lines:
            print("Found ANNUAL already for", last_name, date_of_report)
            print("Constructing (or adding) to profile...")
            construct_profile(recordString)
            continue
                    
        reports.click()

        time.sleep(1)
        
        close_last_tab()

        annual_headers = checked_find("xpath", "/html/body/div/main/div/div/section[3]/div[2]/table/thead")
        annual_table = checked_find("xpath", "/html/body/div/main/div/div/section[3]/div[2]/table/tbody")

        if annual_headers == None or annual_table == None:
            continue

        rows = annual_table.find_elements(by="tag name", value="tr")
        headers = annual_headers.find_elements(by="tag name", value="tr")
        
        big_list = []
        header_list = []

        for header in headers:
            cols = header.find_elements(by="tag name", value = "th")
            for col in cols:
                header_list.append(col.text)

        for row in rows:
            lil_list = []
            cols = row.find_elements(by="tag name", value = "td")
            for col in cols:
                t = col.text
                if "/" in col.text:
                    t = col.text.replace("/", "-")
                lil_list.append(t)
            big_list.append(lil_list)


        trans_dict = dictify(header_list, big_list)

        df = pandas.DataFrame.from_dict(trans_dict)

        list_of_profiles.append(Profile(last_name, [{date_text: df}]))

        
        print("Date of Report:", date_text)
        print(df)
        print("Done with", last_name)

        df = add_amounts(df)

        if SAVE_TO_CSV:
            print(string)
            df.to_csv(string, index = False)
            record_to_master([[last_name, date_text, string]])



if __name__ == "__main__":
    
    ptr_master_lines = read_master()
    
    [construct_profile(line.strip()) for line in ptr_master_lines]

    if DO_WEBSCRAPE and len(list_of_names) > 0:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        try:
            webScrape(list_of_names)
        except Exception as e:
            print("Error in webscraping")
            raise e
            driver.quit()

    

    





