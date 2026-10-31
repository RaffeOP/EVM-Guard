pragma solidity 0.8.20;

contract Wallet2293 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public shares;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        supply += msg.value;
    }
    address[] public members;

    function join() public {
        if (members.length < 16) members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < 16; i++) {
            if (i < members.length) members[i].code.length;
        }
    }

    function totalDeposits() public view returns (uint256) { return supply; }
}
