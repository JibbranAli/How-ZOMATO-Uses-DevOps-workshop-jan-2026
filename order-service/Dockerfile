FROM golang:1.21-alpine

WORKDIR /app

ENV GO111MODULE=off

COPY main.go .

RUN go build -o main main.go

EXPOSE 3003

CMD ["./main"]

