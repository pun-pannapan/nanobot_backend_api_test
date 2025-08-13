เป็น micro service ที่เป็น 2 service หรือ api
1. User API — ผู้ใช้งานระบบ (Users CRUD), JWT Authentication, WebSocket แจ้งเตือน สำหรับส่วน delete อาจทำเป็น softdelete ก็ได้แต่กรณียังทำเป็น hard delete

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
สำหรับ internal Api การใช้ internal key แทนการใช้ token
จะประโยชน์คือลด network transaction และไม่จำเป็นต้องสร้าง
ีuser สำหรับ internal service integration

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
        INT id PK
        VARCHAR username "UNIQUE INDEX"
        VARCHAR full_name
        VARCHAR email
        TEXT hashed_password
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    EXCHANGE_INFO {
        INT id PK
        VARCHAR symbol "INDEX"
        JSONB exchange_info
        TIMESTAMPTZ called_at
    }


ฐานข้อมูลเพิ่มเติมสำหรับระบบการเทรดเพิ่มเติม
โดยที่ wallet - wallet trans เราเก็บไว้ที่ exchange เป็นหลักแต่เราก็ต้องเก็บ
log ไว้ที่เราด้วย นำโคดไปเปิดได้ใน mermaid live เพื่อแสดง er diagram
https://mermaid.live

erDiagram
    USERS {
        INT id PK
        VARCHAR username "UNIQUE INDEX"
        VARCHAR full_name
        VARCHAR email
        TEXT hashed_password
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    EXCHANGE_INFO {
        INT id PK
        VARCHAR symbol "INDEX"
        JSONB exchange_info
        TIMESTAMPTZ called_at
    }

    ASSETS {
        smallint id PK
        varchar code "e.g. BTC"
        varchar name
        int8 base_precision "จำนวนทศนิยมของสินทรัพย์"
    }

    SYMBOLS {
        int id PK
        varchar symbol "e.g. BTCUSDT"
        int base_asset_id FK
        int quote_asset_id FK
        numeric tick_size
        numeric step_size
        numeric min_notional
        boolean is_active
    }

    ORDERS {
        bigserial id PK
        int user_id FK
        int symbol_id FK
        varchar side "buy/sell"
        varchar order_type "market/limit/stop_limit"
        varchar time_in_force "GTC/IOC/FOK"
        numeric price
        numeric stop_price
        numeric qty
        numeric executed_qty
        varchar status "pending/open/partially_filled/filled/canceled/rejected"
        varchar client_order_id "unique per user (optional)"
        timestamptz created_at "default now()"
        timestamptz updated_at
    }

    TRADES {
        bigserial id PK
        bigint order_id FK
        int symbol_id FK
        numeric price
        numeric qty
        numeric quote_qty
        int fee_asset_id FK
        numeric fee_amount
        timestamptz trade_time "default now()"
    }

    USERS ||--o{ WALLETS : "1..*"

    USERS ||--o{ ORDERS : "1..*"
    SYMBOLS ||--o{ ORDERS : "1..*"
    ORDERS ||--o{ TRADES : "1..*"
    SYMBOLS ||--o{ TRADES : "1..*"
    ASSETS ||--o{ TRADES : "fee asset"

    ASSETS ||--o{ SYMBOLS : "base"
    ASSETS ||--o{ SYMBOLS : "quote"

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
และมี deploy บน Digital Ocean
แต่ไม่ได้ทำ Domain Name หรือ SSL (อาจจะยังไม่จำเป็นสำหรับการทำสำหรับระบบ Test นี้)

1. User API 
Swagger UI On Local : http://localhost:8000/docs
Swagger UI On DevEnv:http://174.138.17.16:8000/docs
u:admin
p:admin1234

Web Socket Local  Endpoint : ws://localhost:8000/ws
Web Socket Devenv Endpoint : ws://174.138.17.16:8000/ws

2. Price API
Swagger UI On Local : http://localhost:8100/docs
Swagger UI On DevEnv:http://174.138.17.16:8001/docs

3. Postgres Database
PG Admin On Local: http://localhost:5050/
้host:postgres
db:appdb
u:postgres
p:postgres1234

4. Run unit test
docker exec -it nanobot_backend_api_test-user_api-1 pytest -q
docker exec -it nanobot_backend_api_test-price_api-1 pytest -q
-----------------------------------------------------------------------------