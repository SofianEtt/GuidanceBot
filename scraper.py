import requests
from bs4 import BeautifulSoup
import string
import datetime
import html2text


#env : directml
class Scraper:
    BASE_URL = "https://gamefaqs.gamespot.com"


    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            )
        }) # Permet de contourner le système anti-bot de gamefaqs
    
    def get_game_by_name(self, name : str):
        searchingPage : str
        if name[0] in string.ascii_letters:
            searchingPage = self.BASE_URL+"/sitemap/game/pc/"+name[0]
        else:
            searchingPage = self.BASE_URL+"/sitemap/game/pc/"+"00"
        
        print(searchingPage)
        response = self.session.get(searchingPage)
        soup = BeautifulSoup(response.text, 'html.parser')
        all_links = soup.find_all('a')
        url= ""
        
        for link in all_links:
            if link.get_text(strip=True).lower() == name.lower() : 
                url = link.get('href')+"/faqs"
        
        return url
        
    def get_game_by_id(self, id : str):
        url = self.BASE_URL+"/"+id
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        print(soup.prettify)
        return self.BASE_URL+"/"+id
    

    def getUrlsGuide(self, idknown, game):
   
        if idknown == False :
            url = self.get_game_by_name(game)
            response = self.session.get(url)
        else:
            url = self.get_game_by_id(game)
            response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        urls = []
        ol_tag = soup.find("ol", class_="list flex col1 stripe guides gf_guides")
        if ol_tag: 
            li_items = ol_tag.find_all("li")
            for li in li_items:
                link = li.find('a', class_="bold")
                #print(link.get_text(strip=True))
                #print(self.BASE_URL+link.get('href'))
                urls.append(self.BASE_URL+link.get('href'))
        
        return urls
    
        

    def getGuide(self, urls, game):
        for url in urls:
            now = datetime.datetime.now()
            timestamp = int(now.timestamp() * 1000)
            response = self.session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            paginateType = soup.find("ul", class_ = "paginate")
            if paginateType:
                current_url = url
                all_text = ""
                while current_url:
                    print(f"Scraping: {current_url}")
                    response = self.session.get(current_url)
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Récupération de la div principale
                    main_div = soup.find("div", class_="ffaq ffaqbody")
                    if main_div:
                        for img in main_div.find_all("img"):
                            img.decompose()

                    ftoc_div = main_div.find("div", class_="ftoc")
                    if ftoc_div:
                        ftoc_div.decompose()

                    h = html2text.HTML2Text()
                    h.ignore_links = False
                    h.ignore_images = True
                    h.body_width = 0

                    html = main_div.decode_contents()
                    markdown = h.handle(html)
                    all_text += markdown + "\n\n"

                    # Vérifier la pagination
                    pagination = soup.find("ul", class_="paginate")
                    next_link = None

                    if pagination:
                        for a in pagination.find_all("a"):
                            if "Next" in a.text:
                                href = a.get("href")
                                if href:
                                    next_link = self.BASE_URL + href
                                    break
                            elif "Last" in a.text:
                                href = a.get("href")
                                if href:
                                    next_link = self.BASE_URL + href
                                    break

                    if next_link:
                        current_url = next_link
                    else:
                        current_url = None
                
                with open ("data/"+game.replace(" ","_")+str(timestamp)+".txt", 'a') as f:
                    f.write(all_text)
            else :
                #faqwrap = soup.find("div", class_ = "faqtext")
                pres = soup.find_all("pre")
                for pre in pres:
                    with open ("data/"+game.replace(" ","_")+str(timestamp)+".txt", 'a') as f:
                        f.write(pre.get_text())


    def test(self, flag : bool, game :str):
        urls = self.getUrlsGuide(flag, game)
        self.getGuide(urls, game)

    
    def get_clean_text_from_div(self, url):
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        main_div = soup.find("div", class_="ffaq ffaqbody")
        if main_div:
            for img in main_div.find_all('img'):
                img.decompose()

        # Récupérer le texte brut, sans balises HTML
        #print(main_div.prettify)
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0
        print(h.handle(main_div.decode_contents()))
        #text = main_div.get_text(separator="\n", strip=True)
        #print(text)


rdr2 = Scraper()
#rdr2.get_clean_text_from_div("https://gamefaqs.gamespot.com/pc/274532-red-dead-redemption-2/faqs/76594/chapter-1-colter")
#rdr2.getUrlsGuide(False, "Red Dead Redemption 2")
rdr2.test(False, "Red Dead Redemption 2")
#print(rdr2.typeGuide("https://gamefaqs.gamespot.com/pc/264257-heavy-rain/faqs/59302"))

