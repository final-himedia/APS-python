from flask import Flask, jsonify, request  # ✅ jsonify 추가
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
# GET: 전체 데이터 예측 -> JSON 반환으로 수정
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
        return jsonify({"error": "No data"}), 404

    df['ds'] = pd.to_datetime(df['ds'])
    df['y'] = df['y'].fillna(0)

    # Prophet 모델 학습 및 예측
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)

    # 결과 DataFrame 일부 컬럼만 선택
    result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    # datetime을 문자열로 변환 (JSON 직렬화 가능하도록)
    result['ds'] = result['ds'].astype(str)

    # JSON 응답
    return jsonify(result.to_dict(orient='records'))

# -------------------------------
# POST: 새 데이터 저장
# -------------------------------
@app.post("/api/predict")
def predict_for_input_date():
    data = request.json

    try:
        input_date = datetime.strptime(data['Date'], "%Y-%m-%d")
        qty = float(data['Qty'])
        price = int(data['Price'])
        mrp = float(data['MRP'])
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid input"}), 400

    # ✅ 1) 기존 데이터 조회
    query = text("""
        SELECT Date AS ds, Qty AS y
        FROM products_sales
        ORDER BY Date
    """)
    df = pd.read_sql(query, engine)
    if df.empty:
        return jsonify({"error": "No data in DB"}), 404

    df['ds'] = pd.to_datetime(df['ds'])
    df['y'] = df['y'].fillna(0)

    # ✅ 2) Prophet 모델 학습
    model = Prophet()
    model.fit(df)

    # ✅ 3) 사용자가 보낸 날짜만 future에 넣어서 예측
    future = pd.DataFrame({'ds': [input_date]})
    forecast = model.predict(future)

    result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
    result['ds'] = result['ds'].astype(str)

    # ✅ 4) 한 건만 JSON으로 반환
    return jsonify(result.iloc[0].to_dict()), 200