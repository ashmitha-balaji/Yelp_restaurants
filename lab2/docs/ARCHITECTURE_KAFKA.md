# Lab 2 — Kafka producer / consumer (reviews)

```mermaid
flowchart LR
  subgraph producers [API services producers]
    ReviewAPI[Review_Service]
  end
  subgraph kafka [Kafka topics]
    T1[review.created]
    T2[review.updated]
    T3[review.deleted]
  end
  subgraph consumers [Workers]
    RW[Review_Worker]
  end
  subgraph data [Data]
    MySQL[(MySQL)]
    Mongo[(MongoDB job status)]
  end
  ReviewAPI -->|publish| T1
  ReviewAPI -->|publish| T2
  ReviewAPI -->|publish| T3
  T1 --> RW
  T2 --> RW
  T3 --> RW
  RW -->|persist ratings| MySQL
  RW -->|mark_done| Mongo
```

Extended diagram (optional topics from assignment): `restaurant.created`, `user.created`, etc., follow the same pattern with dedicated worker services.
