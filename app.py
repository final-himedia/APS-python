from flask import Flask, Response
import io
import matplotlib.pyplot as plt
import pandas as pd
from prophet import Prophet
from sqlalchemy import text
import utils

app = Flask(__name__)

# DB 연결 엔진
engine = utils.get_engine()

# -------------------------------
# GET: 전체 데이터 예측
# -------------------------------
@app.get("/api/predict")
def predict_handle():
    # 데이터 조회
    query = text("""
        SELECT Date AS ds, Qty AS y
        FROM products_sales
        ORDER BY Date
    """)
    df = pd.read_sql(query, engine)
    if df.empty:
        return {"error": "No data"}, 404

    df['ds'] = pd.to_datetime(df['ds'])
    df['y'] = df['y'].fillna(0)

    # Prophet 모델 학습 및 예측
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)

    # 그래프 그리기
    fig, ax = plt.subplots(figsize=(10,6))
    ax.plot(forecast['ds'], forecast['yhat'], label='예측값')
    ax.fill_between(forecast['ds'], forecast['yhat_lower'], forecast['yhat_upper'], color='skyblue', alpha=0.4, label='신뢰구간')
    ax.set_title("Prophet 예측 결과")
    ax.set_xlabel("날짜")
    ax.set_ylabel("예측값")
    ax.legend()

    # PNG 이미지 메모리 버퍼에 저장
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    # 이미지 응답
    return Response(buf.getvalue(), mimetype='image/png')
# -------------------------------
# POST: 새 데이터 저장
# -------------------------------
@app.post("/api/predict")
def insert_handle():
    data = request.json

    try:
        date = datetime.strptime(data['Date'], "%Y-%m-%d")
        qty = float(data['Qty'])
        price = int(data['Price'])
        mrp = float(data['MRP'])
        size = data.get('Size', None)  # 없으면 None
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid input"}), 400

    query = text("""
        INSERT INTO products_sales (Date, Qty, Price, MRP, Size)
        VALUES (:date, :qty, :price, :mrp, :size)
    """)

    with engine.begin() as conn:
        conn.execute(query, {
            "date": date,
            "qty": qty,
            "price": price,
            "mrp": mrp,
            "size": size
        })

    return jsonify({"message": "Data inserted successfully"}), 201
