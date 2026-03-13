# Project Structure

## Mục tiêu

Tách file `main.py` nguyên khối thành kiến trúc module để dễ mở rộng, kiểm thử và bảo trì.

## Thư mục

```text
Nursery-Manager-Project/
├── main.py
├── requirements.txt
├── README.md
├── STRUCTURE.md
├── .env.example
├── config/
│   ├── __init__.py
│   └── settings.py
├── core/
│   ├── __init__.py
│   ├── bot.py
│   ├── constants.py
│   ├── database.py
│   └── helpers.py
├── cogs/
│   ├── __init__.py
│   ├── admin.py
│   ├── classroom.py
│   ├── economy.py
│   ├── games.py
│   └── help.py
└── data/
```

## Trách nhiệm từng phần

- `config/settings.py`: đọc `.env`, gom prefix, owner id và danh sách extension.
- `core/bot.py`: định nghĩa bot chính, load cogs và quản lý kết nối database.
- `core/database.py`: schema và thao tác dữ liệu người dùng.
- `core/helpers.py`: embed, phân quyền và helper lớp học.
- `cogs/admin.py`: lệnh quản trị và sync.
- `cogs/classroom.py`: toàn bộ nghiệp vụ lớp học.
- `cogs/economy.py`: hồ sơ, ngân hàng, điểm danh và thu nhập.
- `cogs/games.py`: race, slot, coinflip.
- `cogs/help.py`: help và global error handling.

## Tương thích dữ liệu

- Nếu `data/nursery_final.db` đã có, bot dùng file đó.
- Nếu chưa có nhưng root đang có `nursery_final.db`, bot vẫn dùng file cũ để tránh làm mất dữ liệu.
- Deployment mới sẽ tạo database trong `data/`.