from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = "postgresql://wvhzcxok:Qqtu_8Myh9l_6W4Ha6FTzOodgK-jmlW2@kandula.db.elephantsql.com/wvhzcxok"
SQLALCHEMY_DATABASE_URL = "postgresql://avnadmin:AVNS_Xxe_HgB7s2J8CneJpNe@pg-b8f450-financial-analysis.i.aivencloud.com:14096/financial_db?sslmode=require"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()