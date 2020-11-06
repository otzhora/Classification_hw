import requests

import pandas as pd
from bs4 import BeautifulSoup


def get_elections_data():
    html = requests.get("http://notelections.online/region/region/st-petersburg?action=show&root=1&tvd=27820001217417&vrn=27820001217413&region=78&global=&sub_region=78&prver=0&pronetvd=null&vibid=27820001217417&type=222")
    if html.status_code != 200:
        raise requests.RequestException

    html = html.content.strip()
    soup = BeautifulSoup(html, "html.parser")
    cics = soup.find_all("a")[8:-3]
    tik_urls = {}
    base_url = "http://notelections.online"
    # get cics urls
    for cic in cics:
        cic_name = cic.contents[0]
        cic_url = f"{base_url}{cic.get('href')}"
        tik_urls[cic_name] = cic_url

    data = []

    for tik_name, tik_url in tik_urls.items():
        if tik_name == "Цифровые избирательные участки":
            break
        # get tik data
        html = requests.get(
            tik_url
        )
        if html.status_code != 200:
            raise requests.RequestException
        html = html.content.strip()
        soup = BeautifulSoup(html, "html.parser")
        tds = soup.find_all("td")[19:]
        # get fields names
        fields = []
        for td in tds[1:32:3]:
            nobr = td.find_all("nobr")[0]
            fields.append(nobr.contents[0])

        # get candidates names
        candidates = []
        for td in tds[36:44:3]:
            nobr = td.find_all("nobr")[0]
            candidates.append(nobr.contents[0])

        # get uiks names
        idx = 45
        uiks = []
        while True:
            nobr = tds[idx].find_all("nobr")[0]
            a = nobr.find_all("a")
            if len(a) == 1:
                uiks.append(a[0].contents[0])
                idx += 1
            else:
                break

        uiks_data = [{} for _ in range(len(uiks))]
        field_idx = 0

        # get uiks data
        while field_idx < len(fields):
            for i in range(len(uiks)):
                nobrs = tds[idx+i].find_all("nobr")[0].b
                uiks_data[i][fields[field_idx]] = int(nobrs.contents[0])
            idx += len(uiks)
            field_idx += 1

        idx += 2
        candidate_idx = 0
        candidates_data = [[0 for _ in range(len(candidates))] for _ in range(len(uiks))]

        # get candidates data
        while candidate_idx < len(candidates):
            for i in range(len(uiks)):
                nobrs = tds[idx+i].find_all("nobr")[0].b
                candidates_data[i][candidate_idx] = int(nobrs.contents[0])
            idx += len(uiks)
            candidate_idx += 1

        for i in range(len(uiks)):
            data.append({
                "tik_name": tik_name,
                "uik_name": uiks[i]
            })
            data[-1].update({
                fields[j]: uiks_data[i][fields[j]]
                for j in range(len(fields))
            })
            data[-1].update({
                candidates[j]: candidates_data[i][j]
                for j in range(len(candidates))
            })
    df = pd.DataFrame(data)
    df.to_csv("election_data.csv")


if __name__ == "__main__":
    get_elections_data()
