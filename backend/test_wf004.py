import requests
import json

try:
    response = requests.post(
        "http://127.0.0.1:8000/api/agent/run",
        data={
            "request": "Generate a product description and SEO metadata for this product.",
            "context": json.dumps({
                "product_name": "Wireless Bluetooth Headphones",
                "category": "Electronics",
                "attributes": "Bluetooth 5.3, ANC, 40-hour battery, over-ear design, black",
                "target_audience": "Students and professionals"
            })
        }
    )
    print("Status Code:", response.status_code)
    try:
        data = response.json()
        print("Response JSON:")
        print(json.dumps(data, indent=2))
        
        # Verify it went to Gemini
        if "execution" in data and data["execution"] and "final_result" in data["execution"]:
            result = data["execution"]["final_result"]
            print("\nKeys in result:", list(result.keys()))
            if "product_description" in result:
                print("\nSUCCESS: WF004 completed with expected shape.")
    except Exception as e:
        print("Could not parse JSON:", response.text)
except Exception as e:
    print("Request failed:", e)
