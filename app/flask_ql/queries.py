import graphene
from graphene import relay, Mutation
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from app.models import User as UserModel, Notes as NoteModel, db
from app import bcrypt
from typing import Optional
from flask_graphql_auth import (
    AuthInfoField,
    GraphQLAuth,
    get_jwt_identity,
    create_access_token,
    create_refresh_token,
    query_header_jwt_required,
    mutation_jwt_refresh_token_required,
    mutation_jwt_required
)


class User(SQLAlchemyObjectType):
    class Meta:
        model = UserModel
        interfaces = (graphene.relay.Node,)


class Note(SQLAlchemyObjectType):
    class Meta:
        model = NoteModel
        interfaces = (graphene.relay.Node,)


class ProtectedNote(graphene.Union):
    class Meta:
        types = (Note, AuthInfoField)


class CreateUser(Mutation):
    class Arguments:
        username = graphene.String()
        email = graphene.String()
        password = graphene.String()

    ok = graphene.Boolean()
    user = graphene.Field(User)

    def mutate(root, info, username, email, password):
        new_user = UserModel(
            username=username,
            email=email,
            password=password)
        db.session.add(new_user)
        db.session.commit()
        ok = True
        return CreateUser(ok=ok, user=new_user)


class AuthMutation(graphene.Mutation):
    access_token = graphene.String()
    refresh_token = graphene.String()

    class Arguments:
        username = graphene.String()
        password = graphene.String()

    def mutate(self, info, username, password):
        user = db.session.query(UserModel).filter_by(username=username, password=password).first()
        print(user)
        if not user:
            raise Exception('Authentication Failure : User is not registered')
        return AuthMutation(
            access_token=create_access_token(username),
            refresh_token=create_refresh_token(username)
        )


class CreateNote(graphene.Mutation):
    note = graphene.Field(ProtectedNote)

    class Arguments:
        title = graphene.String(required=True)
        body = graphene.String(required=True)
        user_id = graphene.Int(required=True)
        token = graphene.String()

    @mutation_jwt_required
    def mutate(self, info, title, user_id, body):
        note = NoteModel(title=title, user_id=user_id, body=body)
        if note:
            db.session.add(note)
            db.session.commit()
        return CreateNote(note=note)


class UpdateNote(Mutation):
    class Arguments:
        note_id = graphene.String()
        title = graphene.String()
        body = graphene.String()
        token = graphene.String(required=True)

    ok = graphene.Boolean()
    note = graphene.Field(Note)

    @mutation_jwt_required
    def mutate(root, info, note_id, title: Optional[str] = None, body: Optional[str] = None):
        note = db.session.query(NoteModel).filter_by(id=note_id).first()
        if not title:
            note.body = body
        if not body:
            note.title = title
        else:
            note.body = body
            note.title = title
        db.session.commit()
        ok = True
        note = note
        return UpdateNote(ok=ok, note=note)


class DeleteNote(Mutation):
    class Arguments:
        note_id = graphene.Int()
        token = graphene.String()

    ok = graphene.Boolean()
    note = graphene.Field(Note)
    token = graphene.String()

    @mutation_jwt_required
    def mutate(root, info, note_id):
        note = db.session.query(NoteModel).filter_by(id=note_id).first()
        if not note:
            return {"Exception": "There is no such note"}
        else:
            db.session.delete(note)
            db.session.commit()
        ok = True
        note = note
        db.session.commit()
        return DeleteNote(ok=ok, note=note)


class RefreshMutation(graphene.Mutation):
    class Arguments:
        refresh_token = graphene.String()

    new_token = graphene.String()

    @mutation_jwt_refresh_token_required
    def mutate(self):
        current_user = get_jwt_identity()
        return RefreshMutation(new_token=create_access_token(identity=current_user))


class AllMutations(graphene.ObjectType):
    CreateUser = CreateUser.Field()
    AuthMutation = AuthMutation.Field()
    CreateNote = CreateNote.Field()
    UpdateNote = UpdateNote.Field()
    DeleteNote = DeleteNote.Field()


class Query(graphene.ObjectType):
    node = graphene.relay.Node.Field()

    all_users = SQLAlchemyConnectionField(User)
    all_notes = SQLAlchemyConnectionField(Note)
    get_note = graphene.Field(type=ProtectedNote, token=graphene.String(), id=graphene.Int())

    @query_header_jwt_required
    def resolve_get_store(self, info, id):
        store_qry = Note.get_query(info)
        storeval = store_qry.filter(NoteModel.id.contains(id)).first()
        return storeval


schema = graphene.Schema(mutation=AllMutations, query=Query)
