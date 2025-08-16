from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json


DB_USER = "root"
DB_PASSWORD = "**1122JjSs**"
DB_HOST = "localhost"
DB_NAME = "shopify_app"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    price = Column(String(50))
    url = Column(Text)


def scrape_products_from_json(shopify_url: str):
    
    products_data = []
    page = 1
    while True:
        
        json_url = f"{shopify_url.rstrip('/')}/products.json?page={page}"
        
        try:
            response = requests.get(json_url, timeout=10)
            response.raise_for_status() 
            data = response.json()
            
            if not data.get('products'):
                break
                
            for product in data['products']:
                product_name = product.get('title', 'Unknown')
                product_url = f"{shopify_url.rstrip('/')}/products/{product.get('handle')}"
          
                product_price = None
                if product.get('variants') and len(product['variants']) > 0:
                    product_price = product['variants'][0].get('price', 'N/A')
                
                products_data.append({
                    "name": product_name,
                    "price": f"${product_price}" if product_price else "N/A",
                    "url": product_url
                })
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from {json_url}: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {json_url}: {e}")
            break
            
    return products_data

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Shopify Scraper API is running!"}

@app.post("/scrape/")
def scrape_and_store(shopify_url: str):
   
    
    Base.metadata.create_all(bind=engine)

    scraped_products = scrape_products_from_json(shopify_url)

    if not scraped_products:
        return {"message": "No products were scraped. Check the URL and try again."}

    db = SessionLocal()
    for product_data in scraped_products:
        new_product = Product(
            name=product_data['name'],
            price=product_data['price'],
            url=product_data['url']
        )
        db.add(new_product)
    
    db.commit()
    db.close()
    
    return {"message": f"Successfully scraped {len(scraped_products)} products."}