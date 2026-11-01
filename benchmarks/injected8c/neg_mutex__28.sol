pragma solidity 0.8.20;

contract Pool9022 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public shares;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        total += msg.value;
    }
    bool private locked;

    function withdraw(uint256 amount) public {
        require(!locked);
        locked = true;
        require(shares[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        shares[msg.sender] -= amount;
        total -= amount;
        locked = false;
    }
}
