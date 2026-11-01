pragma solidity 0.8.20;

contract Bank9151 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public shares;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        total += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(shares[msg.sender] >= amount);
        payable(msg.sender).transfer(amount);
        shares[msg.sender] -= amount;
        total -= amount;
    }

    function totalDeposits() public view returns (uint256) { return total; }
}
