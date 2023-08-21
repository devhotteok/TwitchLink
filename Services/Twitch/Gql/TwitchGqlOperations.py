class TwitchGQLOperation:
    query = ""
    variableList = []

    @classmethod
    def load(cls, variables: dict) -> dict:
        return {"query": cls.query, "variables": {variable: variables.get(variable) for variable in cls.variableList}}


class GetChannel(TwitchGQLOperation):
    query = """
        query($id: ID $login: String) {
          user(id: $id login: $login) {
            id
            login
            displayName
            description
            createdAt
            primaryColorHex
            profileImageURL(width: 300)
            offlineImageURL
            profileURL
            roles {
              isPartner
              isAffiliate
              isStaff
            }
            followers {
              totalCount
            }
            lastBroadcast {
              id
              title
              game {
                id
                name
                boxArtURL
                displayName
              }
              startedAt
            }
            stream {
              id
              title
              game {
                id
                name
                boxArtURL
                displayName
              }
              type
              previewImageURL
              broadcaster {
                id
                login
                displayName
                profileImageURL(width: 300)
                createdAt
              }
              createdAt
              viewersCount
            }
          }
        }
    """

    variableList = [
        "id",
        "login"
    ]


class GetChannelVideos(TwitchGQLOperation):
    query = """
        query($login: String!, $type: BroadcastType, $sort: VideoSort!, $limit: Int!, $cursor: Cursor!) {
          user(login: $login) {
            videos(type: $type, sort: $sort, first: $limit, after: $cursor) {
              edges {
                cursor
                node {
                  id
                  title
                  game {
                    id
                    name
                    boxArtURL
                    displayName
                  }
                  previewThumbnailURL
                  owner {
                    id
                    login
                    displayName
                    profileImageURL(width: 300)
                    createdAt
                  }
                  creator {
                    id
                    login
                    displayName
                    profileImageURL(width: 300)
                    createdAt
                  }
                  lengthSeconds
                  createdAt
                  publishedAt
                  viewCount
                }
              }
              pageInfo {
                hasNextPage
              }
            }
          }
        }
    """

    variableList = [
        "login",
        "type",
        "sort",
        "limit",
        "cursor"
    ]


class GetChannelClips(TwitchGQLOperation):
    query = """
        query($login: String!, $filter: ClipsFilter!, $limit: Int!, $cursor: Cursor!) {
          user(login: $login) {
            clips(criteria: {filter: $filter}, first: $limit, after: $cursor) {
              edges {
                cursor
                node {
                  id
                  title
                  game {
                    id
                    name
                    boxArtURL
                    displayName
                  }
                  thumbnailURL
                  slug
                  url
                  broadcaster {
                    id
                    login
                    displayName
                    profileImageURL(width: 300)
                    createdAt
                  }
                  curator {
                    id
                    login
                    displayName
                    profileImageURL(width: 300)
                    createdAt
                  }
                  durationSeconds
                  createdAt
                  viewCount
                }
              }
              pageInfo {
                hasNextPage
              }
            }
          }
        }
    """

    variableList = [
        "login",
        "filter",
        "limit",
        "cursor"
    ]


class GetVideo(TwitchGQLOperation):
    query = """
        query($id: ID!) {
          video(id: $id) {
            id
            title
            game {
              id
              name
              boxArtURL
              displayName
            }
            previewThumbnailURL
            owner {
              id
              login
              displayName
              profileImageURL(width: 300)
              createdAt
            }
            creator {
              id
              login
              displayName
              profileImageURL(width: 300)
              createdAt
            }
            lengthSeconds
            createdAt
            publishedAt
            viewCount
          }
        }
    """

    variableList = [
        "id"
    ]


class GetClip(TwitchGQLOperation):
    query = """
        query($slug: ID!) {
          clip(slug: $slug) {
            id
            title
            game {
              id
              name
              boxArtURL
              displayName
            }
            thumbnailURL
            slug
            url
            broadcaster {
              id
              login
              displayName
              profileImageURL(width: 300)
              createdAt
            }
            curator {
              id
              login
              displayName
              profileImageURL(width: 300)
              createdAt
            }
            durationSeconds
            createdAt
            viewCount
          }
        }
    """

    variableList = [
        "slug"
    ]