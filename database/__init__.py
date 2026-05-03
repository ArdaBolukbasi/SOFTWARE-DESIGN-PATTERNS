"""
database paketi
===============
Firebase Firestore veritabanı bağlantısını yönetir.
Singleton Pattern ile tek bir bağlantı instance'ı garanti edilir.
"""

from database.firebase_client import FirebaseDB

__all__ = ["FirebaseDB"]
