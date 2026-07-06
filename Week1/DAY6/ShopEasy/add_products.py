import asyncio
import aiohttp

async def add_products():
    async with aiohttp.ClientSession() as session:
        products = [
            {'name': '透明硬殼手機殼', 'price': 99},
            {'name': '磨砂黑色手機殼', 'price': 129},
            {'name': '皮革紋理手機殼', 'price': 159},
            {'name': '碳纖維紋理手機殼', 'price': 149},
            {'name': '防摔氣墊手機殼', 'price': 189},
            {'name': '軍事級防護手機殼', 'price': 249},
            {'name': '卡片收納手機殼', 'price': 179},
            {'name': '磁吸支架手機殼', 'price': 199},
            {'name': '防水防塵手機殼', 'price': 219},
            {'name': '夜光發光手機殼', 'price': 169},
        ]
        
        for i, p in enumerate(products, 1):
            data = {
                'seller_id': 1,
                'name': p['name'],
                'price': p['price'],
                'description': f'優質 iPhone 手機殼，提供完美保護'
            }
            async with session.post('http://localhost:8001/api/seller/products', 
                                   json=data,
                                   headers={'Content-Type': 'application/json'}) as res:
                result = await res.json()
                if result.get('ok'):
                    print(f'✅ ({i}/10) {p["name"]} - 已上架')
                else:
                    print(f'❌ ({i}/10) {p["name"]} - 失敗: {result.get("error")}')

asyncio.run(add_products())
