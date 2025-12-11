# app/controllers/auth_controller.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import hashlib
import hmac

from app.config.database import get_db
from app.models.user import User

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


# ===============================
# 비밀번호 해시/검증 유틸 함수
# ===============================

# 실제 서비스라면 환경변수, 별도 설정 파일 등으로 관리해야 합니다.
PASSWORD_SALT = "PASSWORD_SALT"  # 나중에 꼭 바꾸는 것을 추천합니다.


def hash_password(password: str) -> str:
    """
    평문 비밀번호를 해시 문자열로 변환한다.
    - SHA256 + 고정 salt 사용 (연습용)
    - 진짜 서비스에서는 bcrypt/argon2 같은 강한 해시 알고리즘 사용을 권장.
    """
    to_hash = (PASSWORD_SALT + password).encode("utf-8")
    return hashlib.sha256(to_hash).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    사용자가 입력한 비밀번호(plain_password)가
    DB에 저장된 해시(hashed_password)와 일치하는지 비교한다.
    - hmac.compare_digest 를 사용하여 타이밍 공격 방지.
    """
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


# ===============================
# 현재 로그인한 유저 조회용 헬퍼
# ===============================

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),  # ✅ 이 줄이 핵심
) -> User | None:
    """
    세션에 저장된 user_id 기준으로 현재 로그인한 사용자 반환
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    return db.query(User).filter(User.id == user_id).first()


# ===============================
# 1) 로그인 페이지 (GET)
# ===============================

@router.get("/login", response_class=HTMLResponse, response_model=None)
async def login_page(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    로그인 폼을 보여주는 GET 요청 핸들러.
    - 이미 로그인한 상태라면 직접 로그인 화면을 보여줄 필요가 없으므로
      대시보드 선택 페이지(/home)로 곧바로 보낸다.
    """
    current = get_current_user(request, db)
    if current:
        # 이미 로그인 상태면 선택 페이지로 보내기
        return RedirectResponse(url="/home", status_code=302)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": None,  # 초기에는 에러 메시지 없음
        },
    )


# ===============================
# 2) 로그인 처리 (POST)
# ===============================

@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    로그인 폼에서 전송된 아이디/비밀번호를 검증하고,
    성공하면 세션에 user_id, username, role 을 저장한다.
    이후에는 '어느 대시보드로 갈지 선택하는 페이지(/home)'로 이동.
    """
    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    # 아이디가 없거나, 비밀번호가 틀린 경우
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "아이디 또는 비밀번호가 올바르지 않습니다.",
            },
            status_code=400,
        )

    # 로그인 성공 → 세션에 정보 저장
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role

    # 홈 화면으로 리다이렉트
    return RedirectResponse(url="/home", status_code=302)


# ===============================
# 3) 로그아웃
# ===============================

@router.get("/logout")
async def logout(request: Request):
    """
    세션에 저장된 로그인 정보를 모두 삭제하고 로그인 페이지로 리다이렉트한다.
    """
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


# ===============================
# 4) 회원가입 페이지 (GET)
# ===============================

@router.get("/signup", response_class=HTMLResponse, response_model=None)
async def signup_page(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    회원가입 폼을 보여주는 GET 요청 핸들러.
    - 이미 로그인된 상태에서 회원가입 페이지 접근을 막고 싶다면
      현재처럼 로그인 상태 여부를 체크하여 /home 으로 리다이렉트한다.
    """
    current = get_current_user(request, db)
    if current:
        # 이미 로그인 상태라면 굳이 회원가입이 필요 없으므로 선택 페이지로 이동
        return RedirectResponse(url="/home", status_code=302)

    return templates.TemplateResponse(
        "signup.html",
        {
            "request": request,
            "error": None,
        },
    )


# ===============================
# 5) 회원가입 처리 (POST)
# ===============================

@router.post("/signup", response_class=HTMLResponse)
async def signup_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    회원가입 폼에서 전송된 아이디/비밀번호를 검증하고,
    users 테이블에 새 사용자를 생성한다.
    - role 은 기본적으로 'user' 로 저장한다.
    """

    # 1) 간단한 유효성 검증 (원하면 더 강화 가능)
    if not username or not password:
        return templates.TemplateResponse(
            "signup.html",
            {
                "request": request,
                "error": "아이디와 비밀번호를 모두 입력해 주세요.",
            },
            status_code=400,
        )

    if password != password_confirm:
        return templates.TemplateResponse(
            "signup.html",
            {
                "request": request,
                "error": "비밀번호와 비밀번호 확인이 일치하지 않습니다.",
            },
            status_code=400,
        )

    if len(password) < 4:
        return templates.TemplateResponse(
            "signup.html",
            {
                "request": request,
                "error": "비밀번호는 최소 4자 이상이어야 합니다.",
            },
            status_code=400,
        )

    # 2) 아이디 중복 체크
    existing = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if existing:
        return templates.TemplateResponse(
            "signup.html",
            {
                "request": request,
                "error": "이미 존재하는 아이디입니다.",
            },
            status_code=400,
        )

    # 3) 새 유저 생성
    new_user = User(
        username=username,
        password_hash=hash_password(password),
        # role 은 DB DEFAULT 'user' 를 사용하거나, 아래처럼 명시적으로 지정해도 된다.
        role="user",
    )

    db.add(new_user)
    db.commit()

    # 회원가입 성공 후에는 로그인 페이지로 이동
    return RedirectResponse(url="/login", status_code=302)

# ===============================
# 6) 로그인 후 대시보드 선택 페이지
# ===============================

@router.get("/home", response_class=HTMLResponse, response_model=None)
async def home_page(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    로그인 성공 후 이동하는 '대시보드 선택' 페이지.
    - 실제 로봇 대시보드(/dashboard)
    - 시뮬레이션 대시보드(/simulation)
    두 링크/버튼을 제공한다.
    - 로그인하지 않은 상태로 접근하면 /login 으로 보낸다.
    """
    current = get_current_user(request, db)
    if not current:
        # 로그인하지 않은 상태라면 로그인 페이지로
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "username": current.username,
            "role": current.role,
        },
    )