/*
 *   Copyright (c) 2016 In-Q-Tel, Inc, All Rights Reserved.
 *
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 *
 * Uses flowtbag package to parse pcap files for netflow info
 * and sends produced csv to analysis modules with rabbitmq.
 *
 * Created on August 3, 2016
 * @author: lanhamt
 *
 * IMPORTANT NOTE: The first argument when the program is invoked
 * should be the name of the pcap file.

 * rabbitmq:
 *     host:       poseidon-rabbit
 *     exchange:   topic-poseidon-internal
 *         keys:   poseidon.flowparser
 */

package main

import (
    "bufio"
    "fmt"
    "log"
    "os"
    "os/exec"
    "time"

    "github.com/streadway/amqp"
)

const (
    RABBIT_HOST = "poseidon-rabbit"
    RABBIT_EXCH = "topic-poseidon-internal"
    RABBIT_KEYS = "poseidon.flowparser"
)

/*
 * Given an error and message to display on error,
 * checks that an error has occurred; if so, logs a
 * fatal error, panics, and exits.
 */
func failOnError(err error, msg string) {
    if err != nil {
        log.Fatalf("%s: %s", msg, err)
        panic(fmt.Sprintf("%s: %s", msg, err))
    }
}

/*
 * Checks if error has occured from err, prints error message if so
 * and returns false, otherwise prints success message and returns
 * true.
 */
func CheckError(err error, success_msg string, error_msg string) bool {
    if err != nil {
        log.Println(error_msg)
        return false
    } else {
        log.Println(success_msg)
        return true
    }
}

/*
 * Handles connection to rabbitmq broker. Connects to rabbitmq,
 * establishes channel, declares exchange and then declares queues
 * from the program arguments. Retries on connection and channel
 * attempts after sleeping for 2 sec if failure. Returns the
 * connection and channel.
 */
func RabbitConnect() (*amqp.Connection, *amqp.Channel) {
    var conn *amqp.Connection
    var err error
    for {
        conn, err = amqp.Dial("amqp://guest:guest@" + RABBIT_HOST + ":5672/")
        if CheckError(err,
            "connected to rabbitmq",
            "could not connect to rabbitmq, retrying...") {
            break
        } else {
            time.Sleep(time.Second * 2)
        }
    }

    var ch *amqp.Channel
    for {
        ch, err = conn.Channel()
        if CheckError(err,
            "channel connected",
            "could not establish rabbitmq channel, retrying...") {
            break
        } else {
            time.Sleep(time.Second * 2)
        }
    }

    err = ch.ExchangeDeclare(
        RABBIT_EXCH, // name
        "topic",     // type
        false,        // durable
        false,       // auto-deleted
        false,       // internal
        false,       // no-wait
        nil,         // args
    )
    failOnError(err, "failed to declare exchange, exiting")

    return conn, ch
}

/*
 * Sends given line to given rabbitmq channel.
 */
func sendLine(line string, ch *amqp.Channel) {
    err := ch.Publish(
        RABBIT_EXCH, // exchange
        RABBIT_KEYS, // routing key
        false,       // mandatory
        false,       // immediate
        amqp.Publishing{
            ContentType: "text/plain",
            Body:        []byte(line)})
    if err != nil {
        log.Println("failed to send message: " + line)
    } else {
        log.Println(" [*] Sent " + line)
    }
}

/*
 * Connects to rabbitmq, then uses flowtbag to parse pcap
 * file and sends parsed csv to rabbit.
 */
func main() {
    conn, ch := RabbitConnect()
    defer ch.Close()
    defer conn.Close()

    file_name := os.Args[1]
    output_file := file_name + ".csv"
    cmd := exec.Command("./flowtbag", file_name)
    out_fd, err := os.OpenFile(output_file, os.O_WRONLY | os.O_CREATE | os.O_TRUNC, 0777)
    cmd.Stdout = out_fd
    cmd.Run()
    failOnError(err, "failed to parse pcap")

    file, err := os.Open(output_file)
    failOnError(err, "failed to open file")
    defer file.Close()

    scanner := bufio.NewScanner(file)
    for scanner.Scan() {
        sendLine(scanner.Text(), ch)
    }
    sendLine("EOF -- FLOWPARSER FINISHED with file " + file_name, ch)
    failOnError(scanner.Err(), "failed to read file")
}
