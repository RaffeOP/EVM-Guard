pragma solidity 0.5.12;

contract Ledger6988 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public shares;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        supply += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(shares[msg.sender] >= amount);
        msg.sender.transfer(amount);
        shares[msg.sender] -= amount;
        supply -= amount;
    }

    function balanceOf(address who) public view returns (uint256) { return shares[who]; }
}
