from fastapi import APIRouter, HTTPException, Depends, status
from app.user.user_schema import User, UserLogin, UserUpdate, UserDeleteRequest
from app.user.user_service import UserService
from app.dependencies import get_user_service
from app.responses.base_response import BaseResponse

user = APIRouter(prefix="/api/user")


@user.post("/login", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def login_user(user_login: UserLogin, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    try:
        user = service.login(user_login)
        return BaseResponse(status="success", data=user, message="Login Success.") 
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@user.post("/register", response_model=BaseResponse[User], status_code=status.HTTP_201_CREATED)
def register_user(user: User, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    새로운 사용자를 등록하는 엔드포인트.

    Args:
        user (User): 등록할 사용자 정보 (email, password, username)
        service (UserService): 의존성 주입으로 받은 UserService 인스턴스

    Returns:
        BaseResponse[User]: 등록 성공 시 사용자 정보와 성공 메시지를 담은 응답

    Raises:
        HTTPException: 이미 존재하는 이메일일 경우 400 에러 반환
    """
    try:
        new_user = service.register_user(user)
        return BaseResponse(status="success", data=new_user, message="User registration Success.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@user.delete("/delete", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def delete_user(user_delete_request: UserDeleteRequest, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    이메일을 기준으로 사용자를 삭제하는 엔드포인트.

    Args:
        user_delete_request (UserDeleteRequest): 삭제할 사용자의 이메일 정보
        service (UserService): 의존성 주입으로 받은 UserService 인스턴스

    Returns:
        BaseResponse[User]: 삭제 성공 시 삭제된 사용자 정보와 성공 메시지를 담은 응답

    Raises:
        HTTPException: 이메일에 해당하는 사용자가 존재하지 않을 경우 404 에러 반환
    """
    try:
        deleted_user = service.delete_user(user_delete_request.email)
        return BaseResponse(status="success", data=deleted_user, message="User Deletion Success.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@user.put("/update-password", response_model=BaseResponse[User], status_code=status.HTTP_200_OK)
def update_user_password(user_update: UserUpdate, service: UserService = Depends(get_user_service)) -> BaseResponse[User]:
    """
    사용자의 비밀번호를 업데이트하는 엔드포인트.

    Args:
        user_update (UserUpdate): 이메일과 새 비밀번호 정보
        service (UserService): 의존성 주입으로 받은 UserService 인스턴스

    Returns:
        BaseResponse[User]: 업데이트 성공 시 변경된 사용자 정보와 성공 메시지를 담은 응답

    Raises:
        HTTPException: 이메일에 해당하는 사용자가 존재하지 않을 경우 404 에러 반환
    """
    try:
        update_user = service.update_user_pwd(user_update)
        return BaseResponse(status="success", data=update_user, message="User password update success.")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
