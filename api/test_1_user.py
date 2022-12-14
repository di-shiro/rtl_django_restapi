# テストファイル名は、必ず少文字にする！

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = '/api/create/'
PROFILE_URL = '/api/profile/'
TOKEN_URL = '/api/auth/'


# Token認証を通った場合のテストケース（以下のクラス名は、適当にテストに相応しい名前をつけている）
# 各テストケースは、メソッドの形で記載する。
class AuthorizedUserApiTests(TestCase):
    # 下のsetup()関数の内容が毎回実行される。
    # この中で、強制的にユーザの認証を通す処理を記載する。
    def setUp(self):
        # ダミーのユーザ情報を使って、テスト用のユーザを新規作成しておく。
        self.user = get_user_model().objects.create_user(username='dummy', password='dummy_pw')
        # REST Api 自体はサーバ側の機能であり、
        # クライアント側から、例えばGETメソッドやPOSTメソッド等でアクセスを受けて
        # レスポンス（応答）を返すので、テスト用のクライアントを作成しておく。
        self.client = APIClient()

        # 上記にて作成したユーザ情報を用いて、新規User（テスト用クライアント）の認証を強制的に通す
        self.client.force_authenticate(user=self.user)


    # ********** ********** **********
    # 新規Userでログイン後、profileデータが取得できるかのテスト（ログインは上の setup()関数で既に行っている）
    def test_1_1_should_get_user_profile(self):
        res = self.client.get(PROFILE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # APIから受け取ったResponseデータと、予めsetup関数で新規User作成した際の返却値を比較して同じなら正常。
        self.assertEqual(res.data, {
            'id': self.user.id,
            'username': self.user.username,
        })


    # ********** ********** **********
    # PUTメソッドがエラーになるかのテスト
    # views.pyのProfileUserView にて、Profileの PUT と PATCH を無効化しているので、
    # ProfileエンドポイントからのResponseデータのステータスが、405_METHOD_NOT_ALLOWED ならば正常。
    def test_1_2_should_not_allowed_by_PUT(self):
        payload = {
            'username': 'dummy',
            'password': 'dummy_pw',
        }
        res = self.client.put(PROFILE_URL, payload=payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


    # ********** ********** **********
    # PATCHメソッドがエラーになるかのテスト     # 上記のPUTと同じ。
    # views.pyのProfileUserView にて、Profileの PUT と PATCH を無効化しているので、
    # ProfileエンドポイントからのResponseデータのステータスが、405_METHOD_NOT_ALLOWED ならば正常。
    def test_1_3_should_not_allowed_by_PATCH(self):
        payload = {
            'username': 'dummy',
            'password': 'dummy_pw',
        }
        res = self.client.patch(PROFILE_URL, payload=payload)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


# Token認証が通っていないユーザに対するテスト
class UnauthorizedUserApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()


    # ********** ********** **********
    # 新規ユーザが想定通りに作れるかどうか
    def test_1_4_should_create_new_user(self):
        payload = {
            'username': 'dummy',
            'password': 'dummy_pw',
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # DBからログインユーザのパスワード（ハッシュ化されたPassword）を取ってくる。
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(
            user.check_password(payload['password'])
        )
        # responseのデータの中にパスワードが存在しないことを確認する。
        self.assertNotIn('password',res.data)


    # ********** ********** **********
    # 新規ユーザを作成する際、ユーザ名が既に登録済みの場合にエラーとなって弾かれるかテスト
    def test_1_5_should_not_created_user_by_same_credentials(self):
        payload = {
            'username': 'dummy',
            'password': 'dummy_pw',
        }
        # 関数の引数として辞書型を渡す際には **payload として渡す。
        get_user_model().objects.create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    # ********** ********** **********
    # 新規ユーザ登録の歳、設定するpasswordが５文字以上でなければ
    # エラーになって新規ユーザを作成できないことをテスト
    def test_1_6_should_not_create_user_with_short_pw(self):
        # わざとpasswordを2文字にして新規User作成を試す。
        payload = {
            'username': 'dummy',
            'password': 'pw'
        }
        res = self.client.post(CREATE_USER_URL, payload)
        # APIのResponseが400番なら正常にPassのバリデーションが動作していることが確認できる。
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    # ********** ********** **********
    # TOKEN 関連
    # responseデータの中に、想定通りにTOKENが含まれているかをテスト
    def test_1_7_should_response_token(self):
        payload = {
            'username': 'dummy',
            'password': 'pw'
        }
        # テスト用に新しくユーザを１つ作っておく。create_userで新規作成
        get_user_model().objects.create_user(**payload)
        # 上で新規作成したUser（テスト用ユーザ）を使ってTOKENデータを取得する
        res = self.client.post(TOKEN_URL, payload)
        # 取得したTOKENデータの中に token という文字が含まれていればTrueを返す。
        self.assertIn('token', res.data)
        # responseのステータスが200番になっているか
        self.assertEqual(res.status_code, status.HTTP_200_OK)


    # ********** ********** **********
    # ここでは、既存Userでパスワードをわざと間違えてアクセスする
    # ユーザ名は正しいが、パスワードのみ間違った場合、正常な処理としてエラーを返すかテストしている。
    # エラーとなってTOKENが生成されず、ステータスが400_Bad_request となれば正常。
    def test_1_8_should_not_response_token_with_invalid_credentials(self):
        get_user_model().objects.create_user(username='dummy', password='dummy_pw')
        payload = {
            'username': 'dummy',
            'password': 'wrong'
        }
        res = self.client.post(TOKEN_URL, payload)

        # responseデータの中に tokenフィールド(tokenという文字)が含まれていないなら正常。
        self.assertNotIn('token', res.data)
        # ステータスが 400_BAD_REQUEST になるなら正常。
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    # ********** ********** **********
    # 存在しないユーザのユーザ名とパスワードでTOKENを生成しようとした場合、エラーを返すかテスト
    # ここでは、予め新規ユーザを作成せずに、DBに存在しないユーザ名とパスワードで、
    # いきなりTOKENのエンドポイントにアクセスする。
    # エラーとなってTOKENが生成されず、ステータスが400_Bad_request となれば正常。
    def test_1_9_should_not_response_token_with_non_exist_credentials(self):
        payload = {
            'username': 'dummy',
            'password': 'wrong'
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    # ********** ********** **********
    # パスワードのみ空の状態でTOKENエンドポイントにアクセスした場合、エラーを返すかテスト
    def test_1__10_should_not_response_token_with_missing_field(self):
        payload = {
            'username': 'dummy',
            'password': ''          # パスワードのみ空にしておく
        }
        res = self.client.post(TOKEN_URL, payload=payload)

        # responseデータの中にTOKENフィールドが存在せず（tokenという文字列が含まれないこと）、
        # ステータスが400_BAD_REQUEST になれば正常
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    # ********** ********** **********
    # ユーザ名とパスワードの２つが空の状態でTOKENエンドポイントにアクセスした場合、エラーを返すかテスト
    def test_1__11_should_not_response_token_with_missing_field(self):
        payload = {
            'username': '',
            'password': ''
        }
        res = self.client.post(TOKEN_URL, payload=payload)

        # responseデータの中にTOKENフィールドが存在せず（tokenという文字列が含まれないこと）、
        # ステータスが400_BAD_REQUEST になれば正常
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    # ********** ********** **********
    # TOKEN認証に通っていない状態で、Profile/エンドポイントにアクセスした場合、
    # エラーとなりアクセスできないならば正常
    def test_1__12_should_not_get_user_profile_when_unauthorized(self):
        res = self.client.get(PROFILE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

