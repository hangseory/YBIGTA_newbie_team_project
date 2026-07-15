from app.user.user_repository import UserRepository
from app.user.user_schema import User, UserLogin, UserUpdate

class UserService:
    def __init__(self, userRepoitory: UserRepository) -> None:
        self.repo = userRepoitory

    """
        use function form user_repository.py
    
    """
    def login(self, user_login: UserLogin) -> User:
        ## TODO
        """
        get_user_by_email() returns None if fails

        Class UserLogin from user_schema.py
        """ 
        user = self.repo.get_user_by_email(user_login.email)

        """
        각 예외사항 처리 후 user return
        """
        if user is None:
            raise ValueError("User not Found.")

        if user.password != user_login.password:
            raise ValueError("Invalid ID/PW")

        return user
        
    def register_user(self, new_user: User) -> User:
        ## TODO
        """
        new_user.email 이 기존 user의 email 과 같은지 확인
        존재 하면 exception
        존재 하지 않으면 save_user 후 new_user 반환
        """
        user = self.repo.get_user_by_email(new_user.email)

        if user :
            raise ValueError("User already Exists.")

        """
        save_user 에서 dictionary 에 저장후 
        json 파일에 전체 내용 dump => 느림
        """
        return self.repo.save_user( new_user)

    def delete_user(self, email: str) -> User:
        ## TODO       
        """
        delete 할 email 존재 확인
        없을시 exception
        존재하면 삭제
        """
        deleted_user = self.repo.get_user_by_email( email)

        if not deleted_user :
            raise ValueError("User not Found.")

        return self.repo.delete_user( deleted_user)

    def update_user_pwd(self, user_update: UserUpdate) -> User:
        ## TODO
        """
        update 할 email 존재 확인
        없을시 exception
        존재하면 password update 후 save_user

        이때 update_user : User , user_update : UserUpdate 로 password 만 옮기고 
        update_user 를 save_user 해야함
        """

        updated_user = self.repo.get_user_by_email( user_update.email)

        if not updated_user :
            raise ValueError("User not Found.")
        updated_user.password = user_update.new_password

        return self.repo.save_user( updated_user)
        