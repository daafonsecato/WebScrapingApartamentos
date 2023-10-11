from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class Driver:
    def __init__(self, options, service):
        self.service = service
        self.options = options
        self.webdriver = None

    def add_option(self, argument):
        self.options.add_argument(argument)

    def set_webdriver(self):
        self.webdriver = webdriver.Chrome(
            options=self.options, service=self.service)


def driver():
    driver = Driver(Options(), Service())
    userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.100.0"
    driver.add_option(f"user-agent={userAgent}")
    driver.add_option("--no-sandbox")
    driver.add_option('disable-notifications')
    driver.add_option("--headless")
    driver.set_webdriver()

    return driver


def scrape_property_details():
    driver_instance = driver()
    browser = driver_instance.webdriver
    browser.get(
        "https://www.fincaraiz.com.co/inmueble/casa-en-venta/la-patria/bogota/8268559")

    price = browser.find_element(By.XPATH,
                                 "//p[contains(text(), 'Precio (COP)')]/following-sibling::p").text
    location = browser.find_element(By.XPATH,
                                    "//p[contains(text(), 'Ubicación principal')]/following-sibling::p").text

    description = browser.find_element(
        By.XPATH, "//div[contains(@class, 'MuiBox-root')]//p[contains(text(), 'vende')]").text
    bedrooms = browser.find_element(By.XPATH,
                                    "//p[contains(text(), 'Habitaciones')]/following-sibling::p").text
    bathrooms = browser.find_element(By.XPATH,
                                     "//p[contains(text(), 'Baños')]/following-sibling::p").text
    parking_spaces = browser.find_element(By.XPATH,
                                          "//p[contains(text(), 'Parqueaderos')]/following-sibling::p").text
    built_area = browser.find_element(By.XPATH,
                                      "//p[contains(text(), 'Área construída')]/following-sibling::p").text
    private_area = browser.find_element(By.XPATH,
                                        "//p[contains(text(), 'Área privada')]/following-sibling::p").text
    stratum = browser.find_element(By.XPATH,
                                   "//p[contains(text(), 'Estrato')]/following-sibling::p").text
    age = browser.find_element(By.XPATH,
                               "//p[contains(text(), 'Antigüedad')]/following-sibling::p").text
    floor_number = browser.find_element(By.XPATH,
                                        "//p[contains(text(), 'Piso N°')]/following-sibling::p").text
    admin_fee = browser.find_element(By.XPATH,
                                     "//p[contains(text(), 'Administración')]/following-sibling::p").text
    price_per_m2 = browser.find_element(By.XPATH,
                                        "//p[contains(text(), 'Precio m²')]/following-sibling::p").text

    # Use the XPath to find the elements
    elements = browser.find_elements(
        By.XPATH, "//div[contains(@class, 'MuiBox-root jss791 jss767')]//p[contains(@class, 'jss65 jss73')]")

    # Extract the text from each element
    features_texts = [element.text for element in elements]

    browser.quit()

    return {
        "price": price,
        "location": location,
        "description": description,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "parking_spaces": parking_spaces,
        "built_area": built_area,
        "private_area": private_area,
        "stratum": stratum,
        "age": age,
        "floor_number": floor_number,
        "admin_fee": admin_fee,
        "price_per_m2": price_per_m2,
        "features": features_texts
    }


if __name__ == "__main__":
    details = scrape_property_details()
    print(details)
