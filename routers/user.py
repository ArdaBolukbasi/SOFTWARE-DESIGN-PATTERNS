"""
user.py — Kullanıcı Yönetimi API Endpoint'leri
==================================================
Bu modül, kullanıcı kaydı ve yönetimi ile ilgili endpoint'leri içerir.

    POST /api/register-user

Kullanıcı ilk kez uygulamayı açtığında frontend bu endpoint'i çağırır.
Firestore'da kullanıcı dökümanı yoksa oluşturulur, varsa bilgi mesajı döner.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database.firebase_client import FirebaseDB

router = APIRouter(
    prefix="/api",
    tags=["User Management"],
    responses={
        200: {"description": "Kullanıcı zaten kayıtlı"},
        201: {"description": "Kullanıcı başarıyla oluşturuldu"},
        500: {"description": "Sunucu hatası"},
    },
)

class RegisterUserRequest(BaseModel):
    """
    Kullanıcı kayıt isteğinin gövdesi (request body).

    Attributes:
        user_id: Frontend tarafından sağlanan benzersiz kullanıcı ID'si.
        display_name: Opsiyonel görünen ad.
        email: Opsiyonel e-posta adresi.
    """

    user_id: str = Field(
        ...,
        min_length=1,
        description="Benzersiz kullanıcı ID'si",
        examples=["test_kullanicisi_1"],
    )
    display_name: str = Field(
        default="",
        description="Kullanıcının görünen adı (opsiyonel)",
        examples=["Arda"],
    )
    email: str = Field(
        default="",
        description="Kullanıcının e-posta adresi (opsiyonel)",
        examples=["arda@example.com"],
    )


@router.post("/register-user", status_code=201)
async def register_user(payload: RegisterUserRequest) -> dict[str, Any]:
    """
    Kullanıcıyı Firestore'a kaydeder.

    Frontend uygulamayı her açtığında bu endpoint'i çağırır.
    Kullanıcı zaten veritabanında varsa 200 ile 'Zaten kayıtlı' döner,
    yoksa yeni bir döküman oluşturulur ve 201 döner.

    Bu sayede uygulama açıldığında kullanıcının veritabanında
    hazır olması garanti altına alınır.

    Args:
        payload: RegisterUserRequest — user_id, display_name, email.

    Returns:
        dict: Kayıt durumu ve kullanıcı bilgileri.
    """
    user_id = payload.user_id
    print(f"\n👤 Kullanıcı kayıt isteği: user_id={user_id}")

    try:
        # Singleton pattern ile Firebase bağlantısı al
        firebase_db = FirebaseDB()

        if not firebase_db.is_connected:
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": "Firebase bağlantısı kurulamadı.",
                },
            )

        # Kullanıcının ID ile zaten var olup olmadığını kontrol et
        existing_user = firebase_db.get_document("users", user_id)

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Bu User ID zaten kullanılıyor. Lütfen başka bir tane seçin."
            )
            
        # Display name ve email benzersizliğini kontrol et
        users_ref = firebase_db.client.collection("users")
        
        if payload.display_name:
            name_query = users_ref.where("display_name", "==", payload.display_name).limit(1).get()
            if len(name_query) > 0:
                raise HTTPException(
                    status_code=400,
                    detail="Bu isim (Display Name) zaten kullanılıyor. Lütfen başka bir isim girin."
                )
                
        if payload.email:
            email_query = users_ref.where("email", "==", payload.email).limit(1).get()
            if len(email_query) > 0:
                raise HTTPException(
                    status_code=400,
                    detail="Bu e-posta adresi zaten kullanılıyor. Lütfen başka bir e-posta girin."
                )

        # Yeni kullanıcı dökümanı oluştur
        user_data = {
            "user_id": user_id,
            "display_name": payload.display_name,
            "email": payload.email,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }

        firebase_db.save_document("users", user_data, document_id=user_id)
        print(f"   ✅ Yeni kullanıcı oluşturuldu: {user_id}")

        return {
            "status": "created",
            "message": "Kullanıcı başarıyla kaydedildi.",
            "data": user_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"   ❌ Kullanıcı kayıt hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Kullanıcı kaydı sırasında hata: {str(e)}",
            },
        )


@router.get("/user/{user_id}")
async def get_user(user_id: str) -> dict[str, Any]:
    """
    Belirli bir kullanıcının var olup olmadığını kontrol eder.
    Login (Giriş) işlemi için kullanılır.
    """
    try:
        firebase_db = FirebaseDB()

        if not firebase_db.is_connected:
            raise HTTPException(
                status_code=500,
                detail="Firebase bağlantısı kurulamadı.",
            )

        existing_user = firebase_db.get_document("users", user_id)

        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail="Böyle bir hesap bulunamadı.",
            )

        return {
            "status": "success",
            "data": existing_user,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"   ❌ Kullanıcı kontrol hatası: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Kullanıcı kontrolü sırasında hata: {str(e)}",
        )
