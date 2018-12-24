import graphene
from django.db.models import Q
from graphene_django import DjangoObjectType

from .models import Link, Vote
from users.schema import UserType


class LinkType(DjangoObjectType):
    class Meta:
        model = Link


class VoteType(DjangoObjectType):
    class Meta:
        model = Vote


class Query(graphene.ObjectType):
    links = graphene.List(
        LinkType,
        search=graphene.String(),
        skip=graphene.Int(),
        first=graphene.Int(),
    )
    votes = graphene.List(VoteType)

    def resolve_links(self, info, search=None, skip=None, first=None, **kwargs):
        ls = Link.objects.all()

        if search:
            ls = ls.filter(Q(url__icontains=search) |
                Q(description__icontains=search))

        if skip:
            ls = ls[skip:]

        if first:
            ls = ls[:first]
        return ls

    def resolve_votes(self, info, *args, **kwargs):
        return Vote.objects.all()


class CreateLink(graphene.Mutation):
    id = graphene.Int()
    url = graphene.String()
    description = graphene.String()
    posted_by = graphene.Field(UserType)

    class Arguments:
        url = graphene.String()
        description = graphene.String()

    def mutate(self, info, url, description):
        user = info.context.user or None

        link = Link(url=url, description=description, posted_by=user)
        link.save()

        return CreateLink(
            id=link.id,
            url=link.url,
            description=link.description,
            posted_by=link.posted_by,
        )


class CreateVote(graphene.Mutation):
    link = graphene.Field(LinkType)
    user = graphene.Field(UserType)

    class Arguments:
        link_id = graphene.Int()

    def mutate(self, info, link_id):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('You must be logged in to vote!')

        link = Link.objects.filter(id=link_id).first()
        if not link:
            raise Exception('Invalid link!')

        Vote.objects.create(link=link, user=user)

        return CreateVote(link=link, user=user)


class Mutation(graphene.ObjectType):
    create_link = CreateLink.Field()
    create_vote = CreateVote.Field()
