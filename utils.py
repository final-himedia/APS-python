from sqlalchemy import create_engine

def get_engine():
    db_user = "admin"
    db_password = "1q2w3e4r"
    db_host = "database.cpmkaio4y6nw.ap-northeast-2.rds.amazonaws.com"
    db_port = "3306"
    db_name = "aps"

    db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url)
    return engine
