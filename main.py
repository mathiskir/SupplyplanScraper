from dataclasses import replace
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
import json
import requests

with open("/home/Selenium/config.json") as conf:
    config = json.load(conf)

username = config["username"]
password = config["password"]
telegram_base_url = config["telegram_base_url"]
telegram_bot_token = config["telegram_bot_token"]
telegram_target_chatid = config["telegram_target_chatid"]

table_data = {}
results = {}

today = date.today()
if today.weekday() > 5:
    start = today + timedelta(days=today.weekday() - 5)
else:
    start = today - timedelta(days=today.weekday())
day = str(start.strftime("%d.")).replace("0", "")
month = str(start.strftime("%m.")).replace("0", "")
year = start.strftime("%Y")
calendar_week = day + month + year

options = Options()
options.add_argument("--no-sandbox")
options.headless = True
driver = webdriver.Chrome(
    executable_path="/home/Selenium/chromedriver", options=options
)

driver.get(f"https://{username}:{password}@supplyplan.school.xyz")

driver.implicitly_wait(1)

navbar = driver.find_element(By.XPATH, "/html/frameset/frameset/frame")
driver.switch_to.frame(navbar)

element_select = driver.find_element(
    By.XPATH, "/html/body/table/tbody/tr[4]/td/span/nobr/select"
)
select = Select(element_select)
select.select_by_visible_text("Druck-Kla")

calender_week_select = driver.find_element(
    By.XPATH, "/html/body/table/tbody/tr[2]/td/span/nobr/select"
)
select = Select(calender_week_select)
if select.all_selected_options[0].text == calendar_week:
    pass
else:
    select.select_by_visible_text(calendar_week)

driver.switch_to.default_content()

dataframe = driver.find_element(By.XPATH, "/html/frameset/frameset/frameset/frame[1]")
driver.switch_to.frame(dataframe)


def get_table_info(day, index):
    table = driver.find_element(
        By.XPATH, f"/html/body/center/font[1]/div/p[{index}]/table/tbody"
    )
    rows = table.find_elements(By.TAG_NAME, "tr")
    check_for_td = rows[0].find_elements(By.TAG_NAME, "td")
    if len(check_for_td) == 0:
        available = True
    else:
        available = False
    replacement_to_show = []
   
    if available:
        count = 0
        for row in rows:
            entrys = row.find_elements(By.CLASS_NAME, "list")
            data = [entry.text for entry in entrys]
            table_data.update({count: data})
            count += 1
        for replacement in table_data.values():
            if "9" in replacement[0]:
                if len(replacement_to_show) != 0:
                    if (
                        replacement_to_show[len(replacement_to_show) - 1][0]
                        == "9a, 9b,"
                    ):
                        replacement_to_show[len(replacement_to_show) - 1][0] += "9c, 9d"
                        continue
                replacement_to_show.append(replacement)
        text = ""
        for replacement in replacement_to_show:
            if not replacement[0] == " ":
                cosupport_flag = "Ja" if replacement[13] == "x" else "Nein"
                replacement_flag = "Ja" if replacement[12] == "x" else "Nein"
                text += f"Klasse/n: *{replacement[0]}*, Tag: *{replacement[3]}*; *{replacement[1]}*, Stunden: *{replacement[2]}*, Lehrer: *{replacement[5]}* unterrichet *{replacement[4]}* (Eigentlich {replacement[7]} bei {replacement[8]}), Entfall: *{replacement_flag}*, Mitbetreuung: *{cosupport_flag}*, Mehr: {replacement[9]} {replacement[14]}\n\n"
            else:
                text += f"**Die Klassen Spalte ist leer, konnte keine Daten ermitteln.**\n\n"
    else:
        text = "Vertretungen nicht verfügbar."
    if len(replacement_to_show) == 0 and available:
        text = "Keine Vertretungen für Jahrgang 9."

    results.update({day: text})


days_index = {"Montag": 1, "Dienstag": 3, "Mittwoch": 5, "Donnerstag": 7, "Freitag": 9}
for data in days_index.items():
    get_table_info(data[0], data[1])

driver.close()

for result in results.items():
    for chatid in telegram_target_chatid:
        req = requests.post(
            f"{telegram_base_url}{telegram_bot_token}/sendMessage?chat_id={chatid}&text={result[0]}\n{result[1]}&parse_mode=markdown"
        )
        print(req.status_code)
