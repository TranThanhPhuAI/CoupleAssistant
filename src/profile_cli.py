"""Quản lý hồ sơ cá nhân: sở thích, cờ chia sẻ, gói AI, tính cách (tùy chọn).

    python run.py hoso tao minh                        (hỏi từng bước)
    python run.py hoso tao lan --ten Lan --so-thich ca_phe,yen_tinh,chup_anh --chia-se --dong-y
    python run.py hoso sua minh                        (sửa, giữ phần không đổi)
    python run.py hoso xem minh | ds | xoa minh | danhmuc
"""
import argparse
import sys

import config as cfg
from interests import CATALOG, LABEL
from personality import QUESTIONS, ProfileStore, ask_in_terminal

IDS = list(CATALOG)


def print_catalog():
    group = None
    for i, (iid, (label, g, *_)) in enumerate(CATALOG.items(), 1):
        if g != group:
            print(f"\n  [{g}]")
            group = g
        print(f"   {i:2d}. {label:32s} ({iid})")


def ask_yes(prompt, default=False):
    s = input(f"{prompt} ({'C/k' if default else 'c/K'}): ").strip().lower()
    return default if not s else s in {"c", "co", "có", "y", "yes"}


def ask_interests(current):
    print_catalog()
    cur = ", ".join(str(IDS.index(i) + 1) for i in current)
    s = input(f"\nChọn sở thích (số, cách nhau dấu phẩy){f' [hiện tại: {cur}]' if cur else ''}: ").strip()
    if not s:
        return current
    picked = []
    for tok in s.replace(" ", "").split(","):
        if tok.isdigit() and 1 <= int(tok) <= len(IDS):
            picked.append(IDS[int(tok) - 1])
        elif tok in CATALOG:
            picked.append(tok)
        else:
            print(f"  Bỏ qua '{tok}' (không có trong danh mục)")
    return list(dict.fromkeys(picked))


def show(rec):
    print(f"\nHồ sơ: {rec['display_name']} ({rec['user_id']}) | gói AI: {rec['plan']} "
          f"({cfg.AI_PLANS[rec['plan']]} lượt/ngày)")
    print("  Sở thích:", ", ".join(LABEL[i] for i in rec.get("interests", [])) or "(chưa chọn)")
    print("  Cho người đi cùng dùng sở thích của mình:", "CÓ" if rec.get("share_interests_with_partner") else "KHÔNG (mặc định)")
    print("  Tính cách:", f"có (p = {rec['p']})" if "p" in rec else "chưa làm bảng hỏi")
    print("  Cho người kia xem hồ sơ tính cách:", "CÓ" if rec["consent"].get("share_with_partner") else "KHÔNG")


def create_or_edit(args, store, editing):
    old = store.load(args.user_id) or {}
    if editing and not old:
        sys.exit(f"Chưa có hồ sơ '{args.user_id}'. Tạo bằng: python run.py hoso tao {args.user_id}")
    if not editing and old:
        sys.exit(f"Đã có hồ sơ '{args.user_id}'. Sửa bằng: python run.py hoso sua {args.user_id}")
    interactive = args.so_thich is None and not args.dong_y
    if interactive:
        print("Dữ liệu sở thích và tính cách là dữ liệu cá nhân: chỉ lưu trên máy này, xóa được bất cứ lúc nào.")
        if not ask_yes("Bạn đồng ý lưu hồ sơ?"):
            sys.exit("Không lưu (chưa đồng ý).")
        name = input(f"Tên hiển thị [{old.get('display_name', args.user_id)}]: ").strip() or old.get("display_name")
        interests = ask_interests(old.get("interests", []))
        share = ask_yes("Cho phép AI dùng sở thích của bạn khi người đi cùng hỏi gợi ý?",
                        old.get("share_interests_with_partner", False))
        answers = old.get("answers")
        if ask_yes(f"Làm bảng hỏi tính cách {len(QUESTIONS)} câu (tùy chọn, giúp gợi ý sát hơn)?", False):
            answers = ask_in_terminal()
        share_p = ask_yes("Cho người kia xem hồ sơ tính cách?", old.get("consent", {}).get("share_with_partner", False)) \
            if answers else False
        plan = old.get("plan", "free")
    else:
        if not args.dong_y:
            sys.exit("Thiếu --dong-y: cần đồng ý lưu dữ liệu cá nhân.")
        name = args.ten or old.get("display_name")
        interests = [i for i in (args.so_thich or "").split(",") if i] if args.so_thich is not None else old.get("interests", [])
        share, share_p = args.chia_se, args.chia_se_tinh_cach
        answers = ask_in_terminal() if args.tinh_cach else old.get("answers")
        plan = args.goi or old.get("plan", "free")
    rec = store.save(args.user_id, answers=answers, consent=True, share_with_partner=share_p, interests=interests,
                     share_interests=share, display_name=name, plan=plan)
    print("\nĐã lưu.")
    show(rec)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="run.py hoso", description="Quản lý hồ sơ sở thích cá nhân")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("tao", "sua"):
        p = sub.add_parser(c)
        p.add_argument("user_id")
        p.add_argument("--ten")
        p.add_argument("--so-thich", help="danh sách id, vd ca_phe,yen_tinh (xem: hoso danhmuc)")
        p.add_argument("--chia-se", action="store_true", help="cho AI dùng sở thích khi người đi cùng hỏi")
        p.add_argument("--tinh-cach", action="store_true", help="làm bảng hỏi tính cách")
        p.add_argument("--chia-se-tinh-cach", action="store_true")
        p.add_argument("--goi", choices=list(cfg.AI_PLANS))
        p.add_argument("--dong-y", action="store_true", help="đồng ý lưu dữ liệu cá nhân (bắt buộc khi không hỏi từng bước)")
    for c in ("xem", "xoa"):
        sub.add_parser(c).add_argument("user_id")
    sub.add_parser("ds")
    sub.add_parser("danhmuc")
    args = ap.parse_args()
    store = ProfileStore()
    if args.cmd in ("tao", "sua"):
        try:
            create_or_edit(args, store, editing=args.cmd == "sua")
        except ValueError as e:
            sys.exit(f"Lỗi: {e}")
    elif args.cmd == "xem":
        rec = store.load(args.user_id)
        show(rec) if rec else print(f"Không có hồ sơ '{args.user_id}'")
    elif args.cmd == "xoa":
        print("Đã xóa vĩnh viễn." if store.delete(args.user_id) else f"Không có hồ sơ '{args.user_id}'")
    elif args.cmd == "ds":
        users = store.list_users()
        print("\n".join(f"  {u}" for u in users) if users else "Chưa có hồ sơ nào.")
    else:
        print("Danh mục sở thích (dùng số thứ tự hoặc id):")
        print_catalog()


if __name__ == "__main__":
    main()
