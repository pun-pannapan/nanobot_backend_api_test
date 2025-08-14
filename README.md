เป็น micro service ที่เป็น 2 service หรือ api
1. User API — ผู้ใช้งานระบบ (Users CRUD), JWT Authentication, WebSocket แจ้งเตือน
2. Price API — ดึงราคาสินทรัพย์จาก Binance ที่มีแคช Redis

question - answer.
3. การใช้ FastAPI และ Node.js
งานที่ต้องทำ:
เลือกใช้ FastAPI (Python) หรือ Node.js (Express.js) ในการพัฒนา API จากงานที่ 1 พร้อมอธิบายเหตุผลในการเลือกใช้ และเปรียบเทียบกับอีกทางเลือกหนึ่ง
A. เลือกใช้ FastAPI (Python) สามารถพัฒนาได้อย่างรวดเร็ว ประสิทธิภาพสูง สามารถสร้างเอกสาร Open API ให้อัตโนมัติ ด้วย Swagger UI รองรับฟีเจอร์ WebSocket โดยไม่ต้องใช้ ไลบรารีภายนอก และเป็นการเขียนโปร
แกรมแบบ Strong typing โดยใช้ Pydantic

5. การทำงานร่วมกับ Frontend
งานที่ต้องทำ:
สร้าง endpoint ที่ให้ Frontend สามารถเรียกใช้เพื่อดึงข้อมูลผู้ใช้งานพร้อมกับราคาสกุลเงินดิจิทัลล่าสุดที่ดึงจาก Binance
A. http://localhost:8001/internal/price?limit=5


7. การออกแบบฐานข้อมูลและ Microservices
งานที่ต้องทำ:
ออกแบบโครงสร้างฐานข้อมูลสำหรับจัดเก็บข้อมูลผู้ใช้งานและข้อมูลการเทรด โดยแสดงการออกแบบทั้งแบบ Microservices และ Monolithic อธิบายข้อดีและข้อเสียของแต่ละแบบ และเลือกแบบที่คุณคิดว่าเหมาะสมที่สุด
A. เลือก microserviceเพราะมีข้อดี  มีความยืดหยุ่นในการขยายของแต่ละ service ได้ตาม service ที่มีการใช้งานมาก โดยยังออกแบบให้ใช้ 1 doplet อยู่ โดยมี 1 replica โดยที่เวลา deploy ก็จะลดเวลา downtime ลงได้หรือ near zero downtime แต่เนื่องจากเป็น test exam ไม่ได้เป็นงาน production
จึงไม่ได้ออกแบบแบบ HA ที่จะทำบน 2 doplet และมี service database, cache, และ loadbalance 
หรือ proxy แยก แต่ละ service
โดยระบบที่ทำ test เป็นทำบน 1 doplet 1 replica โดยใช้ nginx ทำหน้าที่เป็น reverse proxy ไปยัง
container ต่างๆ การ scale อาจจะเริ่มจากการทำ scale up ก่อนโดยเพิ่ม resource ของ doplet เข้าไปได้
ในกรณีที่เพิ่มไปสูงสุดแล้วสามารถทำ scale out ได้โดยจะต้องแยกเป็น 2 doplet หรือมากกว่า
แต่จะต้องมีการแยก service ต่างๆออกไปจะได้เป็นทั้ง HA และ scale out เพื่อรองรับ request ที่มากขึ้นได้

การทำแบบ monolith ก็มีข้อดีแต่ไม่ได้นำมาใช้ในกรณีนี้ ข้อดีของ Monolith คือ เราสามารถรวม หลายๆ
service ไว้ในที่เดียวได้ทำให้ maintain ได้ง่ายแต่การ scale up/out ก็จะต้องทำไปพร้อมกันหลาย service
เราอาจรวน service ตามประเภทการใช้งาน หรือหมวดหมู่ ที่มีความสำคัญ ก็ได้เพื่อสะดวกในการ maintain
และพัฒนาต่อไป

ส่วนโครงสร้างของ ของฐานข้อมูลจะเป็นดังนี้

erDiagram
    USERS {
        integer  id PK
        varchar(50) username
        varchar(1000) full_name
        varchar(400) email
        text hashed_password
        timestamptz created_at
        timestamptz updated_at
    }

    EXCHANGE_INFO {
        integer  id PK
        varchar(10) symbol
        text exchange_info
        timestamptz called_at
    }


ฐานข้อมูลเพิ่มเติมสำหรับระบบการเทรดเพิ่มเติม
โดยที่ wallet - wallet trans เราเก็บไว้ที่ exchange เป็นหลักแต่เราก็ต้องเก็บ
log ไว้ที่เราด้วย นำโคดไปเปิดได้ใน mermaid live เพื่อแสดง er diagram
https://mermaid.live

erDiagram
    USERS {
        integer id PK
        varchar(50) username
        varchar(1000) full_name
        varchar(400) email
        text hashed_password
        timestamptz created_at
        timestamptz updated_at
    }

    EXCHANGE_INFO {
        integer id PK
        varchar(10) symbol
        text exchange_info
        timestamptz called_at
    }

    ASSETS {
        integer id PK
        varchar(10) code
        varchar(1000) name
        integer base_precision "Asset precision"
    }

    SYMBOLS {
        integer id PK
        varchar(10) symbol "BTCUSDT"
        integer base_asset_id FK
        integer quote_asset_id FK
        numeric tick_size
        numeric step_size
        numeric min_notional
        boolean is_active
    }

    ORDERS {
        uuid id PK
        int user_id FK
        int symbol_id FK
        int exchange_info_id FK "Reference to market data"
        varchar side "buy/sell"
        varchar order_type "market/limit/stop_limit"
        numeric price
        numeric stop_price
        numeric qty
        numeric executed_qty
        varchar status
        varchar client_order_id
        timestamptz created_at
        timestamptz updated_at
    }

    TRADES {
        uuid id PK
        bigint order_id FK
        int symbol_id FK
        numeric price
        numeric qty
        numeric quote_qty
        int fee_asset_id FK
        numeric fee_amount
        timestamptz trade_time "default now()"
    }

    USERS ||--o{ ORDERS : "1..*"
    SYMBOLS ||--o{ ORDERS : "1..*"
    ORDERS ||--o{ TRADES : "1..1"
    SYMBOLS ||--o{ TRADES : "1..*"
    ASSETS ||--o{ TRADES : "fee asset"
    ASSETS ||--o{ SYMBOLS : "base"
    ASSETS ||--o{ SYMBOLS : "quote"
    EXCHANGE_INFO ||--o{ ORDERS : "1..*"

-----------------------------------------------------------------------------
example for .env value
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres1234
POSTGRES_DB=appdb

# pgAdmin
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin1234

# JWT
JWT_SECRET=punjwtsecrete

# Internal API Key
INTERNAL_API_KEY=punapiinternalkey

# CORS
CORS_ORIGINS=*

# Binance & Price API
BINANCE_BASE_URL=https://testnet.binance.vision
SYMBOLS=BTCUSDT,ETHBTC,ETHUSDT
REFRESH_INTERVAL_SECONDS=60
CACHE_TTL_SECONDS=55

-----------------------------------------------------------------------------
Run docker ใน local ใช้คำสั่ง
docker compose up -d --build

1. User API 
Swagger UI: http://localhost:8000/docs


2. Price API
Swagger UI: http://localhost:8100/docs

3. Postgres Database
PG Admin: http://localhost:5050/

-----------------------------------------------------------------------------