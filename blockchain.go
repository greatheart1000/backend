package main

import (
	"log"
	"math/big"
	"net/http"
	"strconv" // 导入 strconv 包
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

// Block 定义了一个区块的简化结构
type Block struct {
	Number      uint64    `json:"number"`
	Hash        string    `json:"hash"`
	Timestamp   time.Time `json:"timestamp"`
	Transaction []string  `json:"transactions"`
}

// Transaction 定义了一个交易的简化结构
type Transaction struct {
	Hash      string `json:"hash"`
	From      string `json:"from"`
	To        string `json:"to"`
	Value     string `json:"value"`
	Status    string `json:"status"`
}

// Global state with mutex for thread safety
var (
	latestBlockNumber uint64
	mockBlocks        = make(map[string]Block)
	mockTransactions  = make(map[string]Transaction)
	mockPrices        = make(map[string]float64)
	mutex             sync.Mutex
)

// initMockData simulates an initial state
func initMockData() {
	latestBlockNumber = 1000
	mutex.Lock()
	defer mutex.Unlock()
	mockBlocks["0x1"] = Block{
		Number:      1,
		Hash:        "0x1abc...",
		Timestamp:   time.Now().Add(-1 * time.Hour),
		Transaction: []string{"0xTx1"},
	}
	mockTransactions["0xTx1"] = Transaction{
		Hash:   "0xTx1",
		From:   "0xSender",
		To:     "0xReceiver",
		Value:  "1000000000000000000",
		Status: "confirmed",
	}
	mockPrices["ETH"] = 3800.5
	mockPrices["BTC"] = 65000.0
}

// startBlockSync simulates the block synchronization process
func startBlockSync() {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()
	log.Println("Starting block synchronization...")

	for range ticker.C {
		mutex.Lock()
		latestBlockNumber++
		blockHash := "0x" + new(big.Int).SetUint64(latestBlockNumber).Text(16)
		newBlock := Block{
			Number:      latestBlockNumber,
			Hash:        blockHash,
			Timestamp:   time.Now(),
			Transaction: []string{},
		}
		mockBlocks[blockHash] = newBlock
		mutex.Unlock()
		log.Printf("Synced new block: #%d", latestBlockNumber)
	}
}

// getBlockByNumber godoc
// @Summary Get block by number
// @Description Get block details by a given block number
// @ID get-block-by-number
// @Produce json
// @Param number path int true "Block Number"
// @Success 200 {object} Block
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Router /block/{number} [get]
func getBlockByNumber(c *gin.Context) {
	numberStr := c.Param("number")
	number, err := strconv.ParseUint(numberStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid block number format"})
		return
	}

	mutex.Lock()
	defer mutex.Unlock()
	for _, block := range mockBlocks {
		if block.Number == number {
			c.JSON(http.StatusOK, block)
			return
		}
	}
	c.JSON(http.StatusNotFound, gin.H{"error": "Block not found"})
}

// getTxByHash godoc
// @Summary Get transaction by hash
// @Description Get transaction details by a given transaction hash
// @ID get-tx-by-hash
// @Produce json
// @Param hash path string true "Transaction Hash"
// @Success 200 {object} Transaction
// @Failure 404 {object} map[string]string
// @Router /tx/{hash} [get]
func getTxByHash(c *gin.Context) {
	txHash := c.Param("hash")
	mutex.Lock()
	defer mutex.Unlock()
	if tx, ok := mockTransactions[txHash]; ok {
		c.JSON(http.StatusOK, tx)
		return
	}
	c.JSON(http.StatusNotFound, gin.H{"error": "Transaction not found"})
}

// getPrice godoc
// @Summary Get price of a symbol
// @Description Get the current price of a cryptocurrency symbol
// @ID get-price
// @Produce json
// @Param symbol path string true "Symbol"
// @Success 200 {object} map[string]float64
// @Failure 404 {object} map[string]string
// @Router /price/{symbol} [get]
func getPrice(c *gin.Context) {
	symbol := c.Param("symbol")
	mutex.Lock()
	defer mutex.Unlock()
	if price, ok := mockPrices[symbol]; ok {
		c.JSON(http.StatusOK, gin.H{"symbol": symbol, "price": price})
		return
	}
	c.JSON(http.StatusNotFound, gin.H{"error": "Price not available for this symbol"})
}

func main() {
	// Initialize mock data
	initMockData()

	// Start a goroutine for block synchronization
	go startBlockSync()

	// Setup Gin router
	r := gin.Default()

	// Routes
	r.GET("/block/:number", getBlockByNumber)
	r.GET("/tx/:hash", getTxByHash)
	r.GET("/price/:symbol", getPrice)

	log.Println("DeFi backend service is running on :8080")
	if err := r.Run(":8080"); err != nil {
		log.Fatalf("Failed to run server: %v", err)
	}
}
