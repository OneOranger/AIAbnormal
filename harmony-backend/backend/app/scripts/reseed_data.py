"""强制重新生成 mock 数据。"""
from app.storage.bootstrap import force_reseed

if __name__ == "__main__":
    force_reseed()
